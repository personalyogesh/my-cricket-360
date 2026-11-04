import SwiftUI

struct MembershipsView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        NavigationStack {
            List {
                Section("Approved clubs") {
                    if session.approvedClubs.isEmpty {
                        Text("No approved clubs yet.")
                    }
                    ForEach(session.memberships.filter { $0.status == .approved }) { membership in
                        membershipRow(membership)
                    }
                }

                Section("Pending requests") {
                    if session.pendingMemberships.isEmpty {
                        Text("No pending requests.")
                    }
                    ForEach(session.pendingMemberships) { membership in
                        membershipRow(membership)
                    }
                }

                Section("Other") {
                    let others = session.memberships.filter {
                        $0.status != .approved && $0.status != .pending
                    }
                    if others.isEmpty {
                        Text("No rejected or suspended memberships.")
                    }
                    ForEach(others) { membership in
                        membershipRow(membership)
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

    private func membershipRow(_ membership: ClubMembership) -> some View {
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
            } else if membership.status == .pending {
                Image(systemName: "clock")
                    .foregroundStyle(.orange)
            }
        }
    }
}

#Preview("Pending and approved") {
    MembershipsView()
        .environmentObject(AppSession.preview(
            club: .starks,
            memberships: [
                ClubMembership(club: .starks, status: .approved, role: "member"),
                ClubMembership(club: .steelers, status: .pending, role: "member")
            ]
        ))
}
