//
//  LanguageSettingsView.swift
//  TreningsCoach
//
//  Language selector from Profile settings
//

import SwiftUI

struct LanguageSettingsView: View {
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.dismiss) private var dismiss
    @AppStorage("app_language") private var appLanguageCode: String = "en"

    var body: some View {
        LanguageSelectionView { language in
            // LanguageSelectionView already calls L10n.set(language)
            appLanguageCode = language.rawValue
            Task { await authManager.updateProfile(language: language) }
            dismiss()
        }
        .navigationTitle(L10n.language)
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    LanguageSettingsView()
        .environmentObject(AuthManager())
}
