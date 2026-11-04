import SwiftUI

struct SponsorsView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        NavigationStack {
            List {
                if let club = session.selectedClub {
                    Section(club.shortName) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(club.foundingSponsorName)
                                .font(.headline)
                            Text("Visible on iOS and \(club.primaryDomain) after admin approval.")
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 4)
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
        }
    }
}
