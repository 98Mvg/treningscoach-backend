//
//  AudioRecordingManager.swift
//  TreningsCoach
//
//  Manages audio recording for breath analysis
//

import Foundation
import AVFoundation
import AVFAudio

class AudioRecordingManager: NSObject, ObservableObject {
    private var audioRecorder: AVAudioRecorder?
    private var recordingSession: AVAudioSession = AVAudioSession.sharedInstance()

    @Published var isRecording = false
    @Published var hasPermission = false

    private var recordingURL: URL {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return documentsPath.appendingPathComponent("breath_recording.wav")
    }

    override init() {
        super.init()
        setupAudioSession()
    }

    // MARK: - Setup

    private func setupAudioSession() {
        do {
            // Deactivate first to allow category change (prevents error -10875)
            try? recordingSession.setActive(false)
            try recordingSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .mixWithOthers])
            // Don't activate here - let the actual recording/playback activate it
            // try recordingSession.setActive(true)

            if #available(iOS 17.0, *) {
                switch AVAudioApplication.shared.recordPermission {
                case .granted:
                    hasPermission = true
                case .denied:
                    hasPermission = false
                case .undetermined:
                    AVAudioApplication.requestRecordPermission { [weak self] allowed in
                        DispatchQueue.main.async {
                            self?.hasPermission = allowed
                        }
                    }
                @unknown default:
                    hasPermission = false
                }
            } else {
                recordingSession.requestRecordPermission { [weak self] allowed in
                    DispatchQueue.main.async {
                        self?.hasPermission = allowed
                    }
                }
            }
        } catch {
            print("Failed to set up recording session: \(error.localizedDescription)")
        }
    }

    // MARK: - Recording

    func startRecording() throws {
        guard hasPermission else {
            throw RecordingError.noPermission
        }

        // Configure audio session just before recording
        try? recordingSession.setActive(false)
        try recordingSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .mixWithOthers])
        try recordingSession.setActive(true)

        // Delete previous recording if exists
        if FileManager.default.fileExists(atPath: recordingURL.path) {
            try? FileManager.default.removeItem(at: recordingURL)
        }

        // Configure recording settings
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 44100.0,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsBigEndianKey: false,
            AVLinearPCMIsFloatKey: false,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        // Create and start recorder
        audioRecorder = try AVAudioRecorder(url: recordingURL, settings: settings)
        audioRecorder?.delegate = self
        audioRecorder?.record()

        isRecording = true
    }

    func stopRecording() -> URL? {
        guard isRecording else { return nil }

        audioRecorder?.stop()
        isRecording = false

        return recordingURL
    }

    // MARK: - Playback

    func playAudio(from url: URL) {
        do {
            let player = try AVAudioPlayer(contentsOf: url)
            player.play()
        } catch {
            print("Failed to play audio: \(error.localizedDescription)")
        }
    }
}

// MARK: - AVAudioRecorderDelegate

extension AudioRecordingManager: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        if !flag {
            print("Recording failed")
            isRecording = false
        }
    }

    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        print("Recording error: \(error?.localizedDescription ?? "Unknown error")")
        isRecording = false
    }
}

// MARK: - Errors

enum RecordingError: LocalizedError {
    case noPermission
    case recordingFailed

    var errorDescription: String? {
        switch self {
        case .noPermission:
            return "Microphone permission is required to record audio"
        case .recordingFailed:
            return "Failed to start recording"
        }
    }
}
