import SwiftUI

struct SponsorsView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        NavigationStack {
            List {
                if let club = session.selectedClub {
                    Section(club.shortName) {
                        if session.sponsors.isEmpty {
                            Text("No published sponsors yet for this club.")
                                .foregroundStyle(.secondary)
                        }
                        ForEach(session.sponsors) { sponsor in
                            VStack(alignment: .leading, spacing: 6) {
                                Text(sponsor.name)
                                    .font(.headline)
                                if let tagline = sponsor.tagline {
                                    Text(tagline)
                                        .font(.footnote)
                                        .foregroundStyle(.secondary)
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                } else {
                    Text("Select an approved club to view its sponsors.")
                }
            }
            .navigationTitle("Sponsors")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    ClubSwitcher()
                }
            }
            .refreshable { await session.loadSponsors() }
        }
    }
}
