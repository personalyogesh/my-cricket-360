import SwiftUI

struct MembershipsView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        NavigationStack {
            List {
                Section("Your memberships") {
                    if session.memberships.isEmpty {
                        Text("No memberships yet. Request access below.")
                    }
                    ForEach(session.memberships) { membership in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(membership.club.displayName)
                                Text("\(membership.status.rawValue.capitalized) · \(membership.role)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            if membership.status == .approved {
                                Image(systemName: "checkmark.seal.fill")
                                    .foregroundStyle(.green)
                            }
                        }
                    }
                }

                Section("Request access") {
                    ForEach(ClubSlug.allCases) { club in
                        Button("Request \(club.shortName)") {
                            Task { await session.requestMembership(for: club) }
                        }
                        .disabled(session.memberships.contains {
                            $0.club == club && ($0.status == .pending || $0.status == .approved)
                        } || session.isLoading)
                    }
                }

                Section {
                    Text("Each club’s administrators approve independently. Private club data requires an approved membership and server authorization.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Clubs")
            .refreshable { await session.refreshProfile() }
        }
    }
}
