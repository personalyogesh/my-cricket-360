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
    @Published var teams: [TeamDTO] = []
    @Published var fixtures: [FixtureDTO] = []
    @Published var fixturesLoading: Bool = false
    @Published var fixturesError: String?
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

    var pendingMemberships: [ClubMembership] {
        memberships.filter { $0.status == .pending }
    }

    func signUpWithSupabase(email: String, password: String, displayName: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            guard let session = try await SupabaseAuthClient.signUp(
                email: email,
                password: password,
                displayName: displayName
            ) else {
                statusMessage = "Account created. Confirm the email, then sign in."
                return
            }
            applySupabaseSession(session)
            await refreshProfile()
            statusMessage = "Signed up via Supabase (\(SupabaseConfig.projectName))"
        } catch {
            statusMessage = error.localizedDescription
        }
    }

    func signInWithSupabase(email: String, password: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let session = try await SupabaseAuthClient.signIn(email: email, password: password)
            applySupabaseSession(session)
            await refreshProfile()
            statusMessage = "Signed in via Supabase (\(SupabaseConfig.projectName))"
        } catch {
            statusMessage = error.localizedDescription
        }
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
        teams = []
        fixtures = []
        fixturesError = nil
        accessToken = nil
        AuthTokenStore.clear()
    }

    func selectClub(_ club: ClubSlug) {
        guard approvedClubs.contains(club) else { return }
        if selectedClub != club {
            sponsors = []
            teams = []
            fixtures = []
            fixturesError = nil
        }
        selectedClub = club
        persistLastClub()
        Task { await loadClubContent() }
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

    func refreshProfile(allowRefresh: Bool = true) async {
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
                sponsors = []
                teams = []
                fixtures = []
                fixturesError = nil
                self.selectedClub = approvedClubs.first
            } else if selectedClub == nil {
                selectedClub = approvedClubs.first
            }
            persistLastClub()
            await loadClubContent()
        } catch {
            statusMessage = error.localizedDescription
            if case APIClientError.http(401, _) = error {
                if allowRefresh, await refreshSupabaseSession() {
                    await refreshProfile(allowRefresh: false)
                    return
                }
                signOut()
            }
        }
    }

    func loadClubContent() async {
        await loadSponsors()
        await loadTeams()
        await loadFixtures()
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

    func loadTeams() async {
        guard let selectedClub else {
            teams = []
            return
        }
        do {
            teams = try await APIClient.shared.publicTeams(slug: selectedClub.rawValue)
        } catch {
            teams = []
            statusMessage = error.localizedDescription
        }
    }

    func loadFixtures(formatCode: String? = nil) async {
        guard let selectedClub else {
            fixtures = []
            fixturesError = nil
            return
        }
        fixturesLoading = true
        fixturesError = nil
        defer { fixturesLoading = false }
        do {
            let page = try await APIClient.shared.publicFixtures(
                slug: selectedClub.rawValue,
                when: "upcoming",
                formatCode: formatCode
            )
            fixtures = page.items
        } catch {
            fixtures = []
            fixturesError = error.localizedDescription
        }
    }

    private func applySupabaseSession(_ session: SupabaseSessionDTO) {
        accessToken = session.access_token
        AuthTokenStore.save(session.access_token)
        if let refresh = session.refresh_token, !refresh.isEmpty {
            AuthTokenStore.saveRefresh(refresh)
        }
        isSignedIn = true
    }

    private func refreshSupabaseSession() async -> Bool {
        guard let refresh = AuthTokenStore.loadRefresh() else { return false }
        do {
            let session = try await SupabaseAuthClient.refresh(refreshToken: refresh)
            applySupabaseSession(session)
            return true
        } catch {
            return false
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

extension AppSession {
    /// In-memory session for SwiftUI previews. Xcode compile is still required to render them.
    static func preview(
        club: ClubSlug?,
        memberships: [ClubMembership] = [],
        sponsors: [SponsorDTO] = [],
        teams: [TeamDTO] = [],
        fixtures: [FixtureDTO] = []
    ) -> AppSession {
        let session = AppSession()
        session.isSignedIn = true
        session.displayName = "Preview Player"
        session.email = "preview@example.com"
        if memberships.isEmpty, let club {
            session.memberships = [ClubMembership(club: club, status: .approved, role: "member")]
        } else {
            session.memberships = memberships
        }
        session.selectedClub = club
        session.sponsors = sponsors
        session.teams = teams
        session.fixtures = fixtures
        return session
    }
}
