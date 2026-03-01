//
//  AudioPackSyncManager.swift
//  TreningsCoach
//
//  Manifest-as-source-of-truth sync for R2 audio packs.
//  Downloads latest.json → manifest.json, diffs local files by sha256,
//  downloads changed/missing files, deletes stale files when workout is idle.
//

import CryptoKit
import Foundation

// MARK: - R2 JSON Models

struct AudioPackLatest: Codable {
    let latestVersion: String
    let manifestKey: String
    let manifestUrl: String?
    let updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case latestVersion = "latest_version"
        case manifestKey = "manifest_key"
        case manifestUrl = "manifest_url"
        case updatedAt = "updated_at"
    }
}

struct AudioPackManifest: Codable {
    let version: String
    let generatedAt: String
    let voice: String
    let languages: [String]
    let totalFiles: Int
    let totalSizeBytes: Int
    let phrases: [ManifestPhrase]

    enum CodingKeys: String, CodingKey {
        case version
        case generatedAt = "generated_at"
        case voice
        case languages
        case totalFiles = "total_files"
        case totalSizeBytes = "total_size_bytes"
        case phrases
    }
}

struct ManifestPhrase: Codable {
    let id: String
    let en: ManifestPhraseFile?
    let no: ManifestPhraseFile?
}

struct ManifestPhraseFile: Codable {
    let file: String
    let size: Int
    let sha256: String
}

// MARK: - Sync State

enum AudioPackSyncState: String {
    case idle
    case checking
    case downloading
    case cleaning
    case complete
    case failed
}

// MARK: - AudioPackSyncManager

@MainActor
class AudioPackSyncManager: ObservableObject {

    static let shared = AudioPackSyncManager()

    // MARK: - Published State

    @Published var syncState: AudioPackSyncState = .idle
    @Published var lastSyncAt: Date?
    @Published var downloadProgress: (completed: Int, total: Int) = (0, 0)
    @Published var lastError: String?
    @Published private(set) var currentPackVersion: String?
    @Published var manifestPhraseCount: Int = 0

    // MARK: - Persistence Keys

    private let kPackVersion = "audio_pack_current_version"
    private let kManifestHash = "audio_pack_manifest_hash"
    private let kLastSyncAt = "audio_pack_last_sync_at"

    // MARK: - Internal

    private var cachedManifest: AudioPackManifest?
    private let session: URLSession

    private var audioPackRootDirectory: URL {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return docs.appendingPathComponent("audio_pack", isDirectory: true)
    }

    // MARK: - Init

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        config.timeoutIntervalForResource = 120
        self.session = URLSession(configuration: config)

        let defaults = UserDefaults.standard
        self.currentPackVersion = defaults.string(forKey: kPackVersion)
        if let ts = defaults.double(forKey: kLastSyncAt) as Double?, ts > 0 {
            self.lastSyncAt = Date(timeIntervalSince1970: ts)
        }
    }

    // MARK: - Primary Sync

    /// Main entry point. Safe to call multiple times — guards against re-entry.
    /// - Parameter workoutState: controls whether stale cleanup runs (only when idle/complete)
    func syncIfNeeded(workoutState: WorkoutState = .idle) async {
        guard syncState == .idle || syncState == .complete || syncState == .failed else {
            return
        }

        syncState = .checking
        lastError = nil

        do {
            // 1. Fetch latest.json
            let latestURL = URL(string: "\(AppConfig.AudioPack.r2PublicURL)/latest.json")!
            let (latestData, _) = try await session.data(from: latestURL)
            let latest = try JSONDecoder().decode(AudioPackLatest.self, from: latestData)

            // 2. Fetch manifest.json
            let manifestURLString = latest.manifestUrl
                ?? "\(AppConfig.AudioPack.r2PublicURL)/\(latest.manifestKey)"
            guard let manifestURL = URL(string: manifestURLString) else {
                throw SyncError.invalidManifestURL
            }
            let (manifestData, _) = try await session.data(from: manifestURL)
            let manifestHash = sha256Hex(manifestData)

            // 3. Check if anything changed
            let storedHash = UserDefaults.standard.string(forKey: kManifestHash)

            if manifestHash == storedHash && latest.latestVersion == currentPackVersion {
                syncState = .complete
                persistLastSyncAt()
                print("📦 Audio pack up to date (v\(latest.latestVersion))")
                return
            }

            // 4. Parse manifest
            let manifest = try JSONDecoder().decode(AudioPackManifest.self, from: manifestData)
            cachedManifest = manifest
            manifestPhraseCount = manifest.phrases.count

            // 5. Download changed/missing files
            syncState = .downloading
            let downloaded = try await downloadChangedFiles(manifest: manifest)

            // 6. Cleanup stale files (only when not in active workout)
            if workoutState == .idle || workoutState == .complete {
                syncState = .cleaning
                let deleted = cleanupStaleFiles(manifest: manifest, version: manifest.version)
                if deleted > 0 {
                    print("📦 Cleaned \(deleted) stale files")
                }
            }

            // 7. Persist new state
            let defaults = UserDefaults.standard
            defaults.set(manifest.version, forKey: kPackVersion)
            defaults.set(manifestHash, forKey: kManifestHash)
            currentPackVersion = manifest.version
            persistLastSyncAt()
            syncState = .complete

            print("📦 Audio pack synced: v\(manifest.version), \(downloaded) files downloaded")

        } catch {
            lastError = error.localizedDescription
            syncState = .failed
            print("📦 Audio pack sync FAILED: \(error)")
        }
    }

    // MARK: - Download Changed Files

    private func downloadChangedFiles(manifest: AudioPackManifest) async throws -> Int {
        var filesToDownload: [(remotePath: String, localPath: URL, expectedHash: String)] = []

        let versionDir = audioPackRootDirectory.appendingPathComponent(manifest.version, isDirectory: true)

        for phrase in manifest.phrases {
            for lang in manifest.languages {
                guard let phraseFile = languageFile(phrase: phrase, language: lang) else { continue }
                let localURL = versionDir.appendingPathComponent(phraseFile.file)

                if FileManager.default.fileExists(atPath: localURL.path) {
                    if let localHash = sha256HexOfFile(at: localURL), localHash == phraseFile.sha256 {
                        continue // File is current
                    }
                }

                filesToDownload.append((
                    remotePath: phraseFile.file,
                    localPath: localURL,
                    expectedHash: phraseFile.sha256
                ))
            }
        }

        downloadProgress = (0, filesToDownload.count)
        guard !filesToDownload.isEmpty else { return 0 }

        let base = AppConfig.AudioPack.r2PublicURL.trimmingCharacters(in: .whitespacesAndNewlines)
        var downloadedCount = 0

        for (index, entry) in filesToDownload.enumerated() {
            let remoteURL = URL(string: "\(base)/\(manifest.version)/\(entry.remotePath)")!

            do {
                let (data, response) = try await session.data(from: remoteURL)
                guard let http = response as? HTTPURLResponse, http.statusCode == 200, !data.isEmpty else {
                    print("📦 Skip \(entry.remotePath): bad response")
                    continue
                }

                // Verify hash before writing
                let downloadedHash = sha256Hex(data)
                guard downloadedHash == entry.expectedHash else {
                    print("📦 Hash mismatch for \(entry.remotePath), skipping")
                    continue
                }

                let dir = entry.localPath.deletingLastPathComponent()
                try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
                try data.write(to: entry.localPath, options: .atomic)
                downloadedCount += 1
            } catch {
                print("📦 Download error \(entry.remotePath): \(error.localizedDescription)")
            }

            downloadProgress = (index + 1, filesToDownload.count)
        }

        return downloadedCount
    }

    // MARK: - Stale File Cleanup

    /// Remove local files not present in the manifest. Only call when workout is idle/complete.
    /// Returns number of files deleted.
    @discardableResult
    func cleanupStaleFiles(manifest: AudioPackManifest? = nil, version: String? = nil) -> Int {
        let resolvedManifest = manifest ?? cachedManifest
        let resolvedVersion = version ?? currentPackVersion ?? AppConfig.AudioPack.version
        guard let manifest = resolvedManifest else { return 0 }

        // Build set of valid relative paths from manifest
        var validPaths: Set<String> = []
        for phrase in manifest.phrases {
            for lang in manifest.languages {
                if let pf = languageFile(phrase: phrase, language: lang) {
                    validPaths.insert(pf.file)
                }
            }
        }

        let versionDir = audioPackRootDirectory.appendingPathComponent(resolvedVersion, isDirectory: true)
        guard FileManager.default.fileExists(atPath: versionDir.path) else { return 0 }

        let fm = FileManager.default
        guard let enumerator = fm.enumerator(at: versionDir, includingPropertiesForKeys: nil) else { return 0 }

        var deletedCount = 0
        while let fileURL = enumerator.nextObject() as? URL {
            guard fileURL.pathExtension == "mp3" else { continue }
            let relativePath = fileURL.path.replacingOccurrences(of: versionDir.path + "/", with: "")
            if !validPaths.contains(relativePath) {
                try? fm.removeItem(at: fileURL)
                deletedCount += 1
            }
        }

        return deletedCount
    }

    /// Convenience: call after workout ends to catch deferred cleanup.
    func purgeStaleFiles() {
        let deleted = cleanupStaleFiles()
        if deleted > 0 {
            print("📦 Purged \(deleted) stale files")
        }
    }

    // MARK: - Debug / Reset

    /// Delete entire local pack and re-sync from scratch.
    func resetAndResync() async {
        let fm = FileManager.default
        if fm.fileExists(atPath: audioPackRootDirectory.path) {
            try? fm.removeItem(at: audioPackRootDirectory)
        }

        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: kPackVersion)
        defaults.removeObject(forKey: kManifestHash)
        defaults.removeObject(forKey: kLastSyncAt)
        currentPackVersion = nil
        lastSyncAt = nil
        cachedManifest = nil
        syncState = .idle
        downloadProgress = (0, 0)

        await syncIfNeeded(workoutState: .idle)
    }

    /// Total size of local audio pack in bytes.
    func localPackSizeBytes() -> Int64 {
        let fm = FileManager.default
        guard fm.fileExists(atPath: audioPackRootDirectory.path) else { return 0 }
        var totalSize: Int64 = 0
        if let enumerator = fm.enumerator(at: audioPackRootDirectory, includingPropertiesForKeys: [.fileSizeKey]) {
            while let url = enumerator.nextObject() as? URL {
                if let size = try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize {
                    totalSize += Int64(size)
                }
            }
        }
        return totalSize
    }

    /// Count of local MP3 files.
    func localFileCount() -> Int {
        let fm = FileManager.default
        guard fm.fileExists(atPath: audioPackRootDirectory.path) else { return 0 }
        var count = 0
        if let enumerator = fm.enumerator(at: audioPackRootDirectory, includingPropertiesForKeys: nil) {
            while let url = enumerator.nextObject() as? URL {
                if url.pathExtension == "mp3" { count += 1 }
            }
        }
        return count
    }

    // MARK: - Helpers

    private func languageFile(phrase: ManifestPhrase, language: String) -> ManifestPhraseFile? {
        switch language {
        case "en": return phrase.en
        case "no": return phrase.no
        default: return nil
        }
    }

    private func sha256Hex(_ data: Data) -> String {
        let digest = SHA256.hash(data: data)
        return digest.map { String(format: "%02x", $0) }.joined()
    }

    private func sha256HexOfFile(at url: URL) -> String? {
        guard let data = try? Data(contentsOf: url) else { return nil }
        return sha256Hex(data)
    }

    private func persistLastSyncAt() {
        let now = Date()
        lastSyncAt = now
        UserDefaults.standard.set(now.timeIntervalSince1970, forKey: kLastSyncAt)
    }

    enum SyncError: LocalizedError {
        case invalidManifestURL

        var errorDescription: String? {
            switch self {
            case .invalidManifestURL: return "Invalid manifest URL in latest.json"
            }
        }
    }
}
