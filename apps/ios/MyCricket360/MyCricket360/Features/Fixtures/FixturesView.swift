import SwiftUI

private enum FormatFilter: String, CaseIterable, Identifiable {
    case all = "All"
    case t20 = "T20"
    case premier = "Premier League"
    case ht = "HT"

    var id: String { rawValue }

    var formatCode: String? {
        switch self {
        case .all: return nil
        case .t20: return "t20"
        case .premier: return "premier_40"
        case .ht: return "ht"
        }
    }
}

struct FixturesView: View {
    @EnvironmentObject private var session: AppSession
    @State private var filter: FormatFilter = .all

    var body: some View {
        NavigationStack {
            Group {
                if session.selectedClub == nil {
                    ContentUnavailableView(
                        "Choose a club",
                        systemImage: "calendar",
                        description: Text("Upcoming fixtures load for the selected club only.")
                    )
                } else if session.fixturesLoading && session.fixtures.isEmpty {
                    ProgressView("Loading fixtures")
                } else if let fixturesError = session.fixturesError {
                    ContentUnavailableView(
                        "Could not load fixtures",
                        systemImage: "exclamationmark.triangle",
                        description: Text(fixturesError)
                    )
                } else if session.fixtures.isEmpty {
                    ContentUnavailableView(
                        "No upcoming fixtures",
                        systemImage: "calendar.badge.exclamationmark",
                        description: Text("Nothing is scheduled, postponed, or live for this club.")
                    )
                } else {
                    List(session.fixtures) { fixture in
                        NavigationLink {
                            FixtureDetailView(fixtureId: fixture.id, preview: fixture)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("\(fixture.home_team_name) vs \(fixture.away_team_name)")
                                    .font(.headline)
                                Text("\(fixture.format_name) · \(fixture.status)")
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                                Text(fixture.venue)
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Fixtures")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    ClubSwitcher()
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Menu(filter.rawValue) {
                        ForEach(FormatFilter.allCases) { option in
                            Button(option.rawValue) {
                                filter = option
                                Task { await session.loadFixtures(formatCode: option.formatCode) }
                            }
                        }
                    }
                }
            }
            .refreshable { await session.loadFixtures(formatCode: filter.formatCode) }
        }
    }
}

struct FixtureDetailView: View {
    @EnvironmentObject private var session: AppSession
    let fixtureId: UUID
    let preview: FixtureDTO?

    @State private var fixture: FixtureDTO?
    @State private var errorMessage: String?
    @State private var isLoading = false

    var body: some View {
        Group {
            if isLoading && fixture == nil {
                ProgressView("Loading match")
            } else if let errorMessage, fixture == nil {
                ContentUnavailableView(
                    "Match unavailable",
                    systemImage: "exclamationmark.triangle",
                    description: Text(errorMessage)
                )
            } else if let fixture {
                List {
                    Section("Match") {
                        LabeledContent("Home", value: fixture.home_team_name)
                        LabeledContent("Away", value: fixture.away_team_name)
                        LabeledContent("Competition", value: fixture.competition)
                        LabeledContent("Season", value: fixture.season)
                        LabeledContent("Format", value: formatLine(fixture))
                        LabeledContent("Status", value: fixture.status)
                        LabeledContent("Venue", value: fixture.venue)
                        LabeledContent("Starts", value: fixture.starts_at)
                        LabeledContent("Timezone", value: fixture.timezone)
                    }
                    Section("Result") {
                        Text(fixture.result_summary ?? "No result has been entered.")
                    }
                }
            }
        }
        .navigationTitle("Match")
        .task { await load() }
    }

    private func load() async {
        if fixture == nil {
            fixture = preview
        }
        guard let club = session.selectedClub else {
            errorMessage = "Select a club first."
            return
        }
        isLoading = true
        defer { isLoading = false }
        do {
            fixture = try await APIClient.shared.publicFixture(slug: club.rawValue, id: fixtureId)
            errorMessage = nil
        } catch {
            if fixture == nil {
                errorMessage = error.localizedDescription
            }
        }
    }

    private func formatLine(_ fixture: FixtureDTO) -> String {
        if let overs = fixture.overs {
            return "\(fixture.format_name) · \(overs) overs"
        }
        return fixture.format_name
    }
}

#Preview("Upcoming") {
    FixturesView()
        .environmentObject(AppSession.preview(
            club: .starks,
            fixtures: [
                FixtureDTO(
                    id: UUID(),
                    schedule_id: nil,
                    season: "2026",
                    competition: "Sunday League",
                    home_team_id: nil,
                    away_team_id: nil,
                    home_team_name: "Starks First XI",
                    away_team_name: "Visitors",
                    venue: "Starks Ground",
                    starts_at: "2026-06-14T18:00:00Z",
                    timezone: "America/New_York",
                    format_code: "t20",
                    format_name: "T20",
                    overs: 20,
                    status: "scheduled",
                    result_summary: nil
                )
            ]
        ))
}
