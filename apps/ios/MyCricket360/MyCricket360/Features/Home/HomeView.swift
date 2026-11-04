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
                        GroupBox("Founding sponsor") {
                            Text(club.foundingSponsorName)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        GroupBox("Next steps") {
                            Text("Fixtures, teams, finances, and content load from the org-scoped API. Authorization is enforced server-side for organization \(club.organizationId).")
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                    } else {
                        ContentUnavailableView(
                            "Choose a club",
                            systemImage: "sportscourt",
                            description: Text("Approve a membership, then use the club switcher.")
                        )
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
        }
    }
}
