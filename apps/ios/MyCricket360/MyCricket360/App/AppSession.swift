import Combine
import Foundation
import SwiftUI

/// Global session: one user account, multi-club memberships, last club persisted securely.
@MainActor
final class AppSession: ObservableObject {
    @Published var isSignedIn: Bool = false
    @Published var displayName: String = "Guest"
    @Published var memberships: [ClubMembership] = []
    @Published var selectedClub: ClubSlug?

    private let lastClubKey = "mc360.lastSelectedClub"

    init() {
        restoreLastClub()
    }

    var approvedClubs: [ClubSlug] {
        memberships.filter { $0.status == .approved }.map(\.club)
    }

    func signInDemo() {
        // Demo shell only — real auth uses Supabase; authorization remains server-side.
        isSignedIn = true
        displayName = "Demo Player"
        memberships = [
            ClubMembership(club: .starks, status: .approved),
            ClubMembership(club: .steelers, status: .pending),
        ]
        if selectedClub == nil || !(approvedClubs.contains(selectedClub!)) {
            selectedClub = approvedClubs.first
            persistLastClub()
        }
    }

    func signOut() {
        isSignedIn = false
        displayName = "Guest"
        memberships = []
        // Keep last club preference for next sign-in convenience; clear if desired later.
    }

    func selectClub(_ club: ClubSlug) {
        guard approvedClubs.contains(club) else { return }
        selectedClub = club
        persistLastClub()
    }

    func requestMembership(for club: ClubSlug) {
        guard isSignedIn else { return }
        if let idx = memberships.firstIndex(where: { $0.club == club }) {
            if memberships[idx].status == .rejected || memberships[idx].status == .revoked {
                memberships[idx].status = .pending
            }
            return
        }
        memberships.append(ClubMembership(club: club, status: .pending))
    }

    private func persistLastClub() {
        guard let selectedClub else {
            ClubSecureStore.remove(lastClubKey)
            return
        }
        ClubSecureStore.set(selectedClub.rawValue, forKey: lastClubKey)
    }

    private func restoreLastClub() {
        guard let raw = ClubSecureStore.string(forKey: lastClubKey),
              let club = ClubSlug(rawValue: raw)
        else { return }
        selectedClub = club
    }
}
