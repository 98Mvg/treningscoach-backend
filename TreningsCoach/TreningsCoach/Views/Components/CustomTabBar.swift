//
//  CustomTabBar.swift
//  TreningsCoach
//
//  Floating tab bar with matched geometry animation
//

import SwiftUI

enum TabItem: Int, CaseIterable {
    case home, workout, profile

    var icon: String {
        switch self {
        case .home:    return "house.fill"
        case .workout: return "figure.run"
        case .profile: return "person.fill"
        }
    }

    var label: String {
        switch self {
        case .home:    return L10n.home
        case .workout: return L10n.workout
        case .profile: return L10n.profileTab
        }
    }
}

struct CustomTabBar: View {
    @Binding var selectedTab: TabItem
    @Namespace private var tabAnimation

    var body: some View {
        HStack(spacing: 0) {
            ForEach(TabItem.allCases, id: \.rawValue) { tab in
                Button {
                    withAnimation(.spring(response: 0.35, dampingFraction: 0.75)) { selectedTab = tab }
                } label: {
                    VStack(spacing: 4) {
                        Image(systemName: tab.icon)
                            .font(.system(size: 20, weight: selectedTab == tab ? .semibold : .regular))
                            .foregroundColor(selectedTab == tab ? CoachiTheme.primary : CoachiTheme.textTertiary)
                        Text(tab.label)
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(selectedTab == tab ? CoachiTheme.primary : CoachiTheme.textTertiary)
                            .lineLimit(2)
                            .minimumScaleFactor(0.7)
                            .multilineTextAlignment(.center)
                            .frame(maxWidth: .infinity, minHeight: 24)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(
                        Group {
                            if selectedTab == tab {
                                RoundedRectangle(cornerRadius: 14, style: .continuous)
                                    .fill(CoachiTheme.primary.opacity(0.1))
                                    .matchedGeometryEffect(id: "tab_bg", in: tabAnimation)
                            }
                        }
                    )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 10).padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(CoachiTheme.surface.opacity(0.95))
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).stroke(Color.white.opacity(0.06), lineWidth: 1))
                .shadow(color: Color.black.opacity(0.4), radius: 20, y: 10)
        )
        .padding(.horizontal, 14)
    }
}
