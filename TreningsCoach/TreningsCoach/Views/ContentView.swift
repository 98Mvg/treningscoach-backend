//
//  ContentView.swift
//  TreningsCoach
//
//  Minimal voice-first UI inspired by ChatGPT voice mode
//

import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject private var viewModel = WorkoutViewModel()

    var body: some View {
        ZStack {
            // Subtle background gradient
            LinearGradient(
                colors: [.white, Color(.systemGray6)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                // Header - diskré
                VStack(spacing: 4) {
                    Text("Treningscoach")
                        .font(.headline)
                        .foregroundColor(.primary)

                    Text(viewModel.currentPhaseDisplay)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 16)

                Spacer()

                // Midten - tom og pustende
                // Voice Orb - hovedfokus
                VoiceOrbView(
                    state: viewModel.voiceState,
                    action: {
                        if viewModel.isContinuousMode {
                            viewModel.stopContinuousWorkout()
                        } else if viewModel.isRecording {
                            viewModel.stopRecording()
                        } else {
                            // Use continuous mode by default
                            viewModel.startContinuousWorkout()
                        }
                    }
                )
                .disabled(viewModel.isProcessing)

                Spacer()
            }
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK", role: .cancel) { }
            } message: {
                Text(viewModel.errorMessage)
            }
        }
    }
}

// MARK: - Preview

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
