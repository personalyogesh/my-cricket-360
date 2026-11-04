import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    if let club = session.selectedClub {
                        Text(club.displayName)
                            .font(.title.bold())
                        Text("Domain \(club.primaryDomain)")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        GroupBox("Teams") {
                            if session.teams.isEmpty {
                                Text("No public teams yet.")
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            } else {
                                ForEach(session.teams) { team in
                                    Text(team.name)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                }
                            }
                        }
                        GroupBox("Published sponsors") {
                            if session.sponsors.isEmpty {
                                Text("None published yet (founding sponsors remain draft until verified).")
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            } else {
                                ForEach(session.sponsors) { sponsor in
                                    Text(sponsor.name)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                }
                            }
                        }
                        GroupBox("Account") {
                            Text(session.displayName)
                            if let email = session.email {
                                Text(email).font(.footnote).foregroundStyle(.secondary)
                            }
                        }
                    } else {
                        ContentUnavailableView(
                            "Choose a club",
                            systemImage: "sportscourt",
                            description: Text("Request and receive approval, then use the club switcher.")
                        )
                    }
                    if let statusMessage = session.statusMessage {
                        Text(statusMessage)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding()
            }
            .navigationTitle("Home")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    ClubSwitcher()
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Sign out") { session.signOut() }
                }
            }
            .refreshable { await session.refreshProfile() }
        }
    }
}

#Preview("Starks home") {
    HomeView()
        .environmentObject(AppSession.preview(club: .starks))
}
