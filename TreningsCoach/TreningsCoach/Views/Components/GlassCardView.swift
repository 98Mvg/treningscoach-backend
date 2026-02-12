//
//  GlassCardView.swift
//  TreningsCoach
//
//  Glassmorphism card container
//

import SwiftUI

struct GlassCardView<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(20)
            .glassCard()
    }
}
