import Combine
import Foundation
import SwiftUI

/// Global session: one user account, multi-club memberships, last club persisted securely.
@MainActor
final class AppSession: ObservableObject {
    @Published var isSignedIn: Bool = false
    @Published var displayName: String = "Guest"
    @Published var email: String?
    @Published var memberships: [ClubMembership] = []
    @Published var selectedClub: ClubSlug?
    @Published var sponsors: [SponsorDTO] = []
    @Published var statusMessage: String?
    @Published var isLoading: Bool = false

    private let lastClubKey = "mc360.lastSelectedClub"
    private var accessToken: String?

    init() {
        restoreLastClub()
        if let token = AuthTokenStore.load() {
            accessToken = token
            Task { await refreshProfile() }
        }
    }

    var approvedClubs: [ClubSlug] {
        memberships.filter { $0.status == .approved }.compactMap { $0.club }
    }

    func signInWithDevAccount(email: String = "player@example.com", displayName: String = "Demo Player") async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await APIClient.shared.issueDevToken(
                email: email,
                displayName: displayName
            )
            accessToken = response.access_token
            AuthTokenStore.save(response.access_token)
            self.displayName = response.user.display_name
            self.email = response.user.email
            isSignedIn = true
            await refreshProfile()
            statusMessage = response.note
        } catch {
            statusMessage = error.localizedDescription
        }
    }

    func signOut() {
        isSignedIn = false
        displayName = "Guest"
        email = nil
        memberships = []
        sponsors = []
        accessToken = nil
        AuthTokenStore.clear()
    }

    func selectClub(_ club: ClubSlug) {
        guard approvedClubs.contains(club) else { return }
        selectedClub = club
        persistLastClub()
        Task { await loadSponsors() }
    }

    func requestMembership(for club: ClubSlug) async {
        guard let accessToken else {
            statusMessage = "Sign in required"
            return
        }
        isLoading = true
        defer { isLoading = false }
        do {
            _ = try await APIClient.shared.requestMembership(token: accessToken, slug: club.rawValue)
            await refreshProfile()
            statusMessage = "Membership requested for \(club.shortName)"
        } catch {
            statusMessage = error.localizedDescription
        }
    }

    func refreshProfile() async {
        guard let accessToken else { return }
        do {
            let me = try await APIClient.shared.me(token: accessToken)
            isSignedIn = true
            displayName = me.user.display_name
            email = me.user.email
            memberships = me.memberships.compactMap { dto in
                guard let club = ClubSlug(rawValue: dto.organization_slug),
                      let status = MembershipStatus(rawValue: dto.status)
                else { return nil }
                return ClubMembership(club: club, status: status, role: dto.role)
            }
            if let selectedClub, !approvedClubs.contains(selectedClub) {
                self.selectedClub = approvedClubs.first
            } else if selectedClub == nil {
                selectedClub = approvedClubs.first
            }
            persistLastClub()
            await loadSponsors()
        } catch {
            statusMessage = error.localizedDescription
            // Token may be invalid
            if case APIClientError.http(401, _) = error {
                signOut()
            }
        }
    }

    func loadSponsors() async {
        guard let selectedClub else {
            sponsors = []
            return
        }
        do {
            sponsors = try await APIClient.shared.publicSponsors(slug: selectedClub.rawValue)
        } catch {
            sponsors = []
            statusMessage = error.localizedDescription
        }
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
