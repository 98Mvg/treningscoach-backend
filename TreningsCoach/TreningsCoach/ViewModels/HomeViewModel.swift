//
//  HomeViewModel.swift
//  TreningsCoach
//
//  Drives lightweight home-screen state and backend wake-up
//

import Foundation

@MainActor
class HomeViewModel: ObservableObject {
    private let apiService = BackendAPIService.shared

    var greeting: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12: return L10n.goodMorning
        case 12..<17: return L10n.goodAfternoon
        case 17..<22: return L10n.goodEvening
        default: return L10n.goodNight
        }
    }

    func loadData() async {
        // The launch home screen no longer renders workout-history-derived stats,
        // so keep this focused on waking the backend for the next real request.
        apiService.wakeBackend()
    }
}
