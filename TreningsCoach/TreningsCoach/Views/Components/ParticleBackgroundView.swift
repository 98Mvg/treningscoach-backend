//
//  ParticleBackgroundView.swift
//  TreningsCoach
//
//  Floating particle background using Canvas API
//

import SwiftUI

struct Particle: Identifiable {
    let id = UUID()
    var x: CGFloat
    var y: CGFloat
    let size: CGFloat
    let opacity: Double
    let speed: Double
    let phase: Double
}

struct ParticleBackgroundView: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var particles: [Particle] = []
    let particleCount: Int

    init(particleCount: Int = 25) { self.particleCount = particleCount }

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30.0)) { timeline in
            Canvas { context, size in
                let now = timeline.date.timeIntervalSinceReferenceDate
                for particle in particles {
                    if reduceMotion {
                        let rect = CGRect(x: particle.x * size.width, y: particle.y * size.height, width: particle.size, height: particle.size)
                        context.opacity = particle.opacity * 0.5
                        context.fill(Circle().path(in: rect), with: .color(CoachiTheme.textTertiary))
                    } else {
                        let elapsed = now * particle.speed + particle.phase
                        let yOffset = elapsed.truncatingRemainder(dividingBy: 1.2)
                        let adjustedY = (particle.y - yOffset / 1.2).truncatingRemainder(dividingBy: 1.0)
                        let finalY = adjustedY < 0 ? adjustedY + 1.0 : adjustedY
                        let xWobble = sin(elapsed * 2) * 0.01
                        let finalX = particle.x + xWobble
                        let rect = CGRect(x: finalX * size.width, y: finalY * size.height, width: particle.size, height: particle.size)
                        let fadeEdge = min(finalY, 1.0 - finalY) * 5.0
                        let alpha = min(particle.opacity, fadeEdge)
                        context.opacity = max(0, alpha)
                        context.fill(Circle().path(in: rect), with: .color(CoachiTheme.textTertiary))
                    }
                }
            }
        }
        .onAppear {
            particles = (0..<particleCount).map { _ in
                Particle(x: .random(in: 0...1), y: .random(in: 0...1), size: .random(in: 1.5...3.5),
                         opacity: .random(in: 0.08...0.25), speed: .random(in: 0.03...0.08), phase: .random(in: 0...10))
            }
        }
        .allowsHitTesting(false)
    }
}
