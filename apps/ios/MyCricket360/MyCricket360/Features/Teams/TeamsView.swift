import SwiftUI

struct TeamsView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        NavigationStack {
            List {
                if let club = session.selectedClub {
                    Section(club.displayName) {
                        if session.teams.isEmpty {
                            Text("No public teams yet for this club.")
                                .foregroundStyle(.secondary)
                        }
                        ForEach(session.teams) { team in
                            VStack(alignment: .leading, spacing: 4) {
                                Text(team.name)
                                    .font(.headline)
                                if let detail = [team.division, team.season].compactMap({ $0 }).joined(separator: " · ").nilIfEmpty {
                                    Text(detail)
                                        .font(.footnote)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                } else {
                    Text("Select an approved club to view its teams.")
                }
            }
            .navigationTitle("Teams")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    ClubSwitcher()
                }
            }
            .refreshable { await session.loadTeams() }
        }
    }
}

private extension String {
    var nilIfEmpty: String? { isEmpty ? nil : self }
}

#Preview("Starks teams") {
    TeamsView()
        .environmentObject(AppSession.preview(club: .starks, teams: [
            TeamDTO(id: UUID(), name: "Starks First XI", division: "Premier", season: "2026")
        ]))
}
