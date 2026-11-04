import SwiftUI

struct ClubSwitcher: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        Menu {
            ForEach(session.approvedClubs) { club in
                Button {
                    session.selectClub(club)
                } label: {
                    if session.selectedClub == club {
                        Label(club.shortName, systemImage: "checkmark")
                    } else {
                        Text(club.shortName)
                    }
                }
            }
            if session.approvedClubs.isEmpty {
                Text("No approved clubs yet")
            }
        } label: {
            Label(
                session.selectedClub?.shortName ?? "Select club",
                systemImage: "arrow.left.arrow.right.circle"
            )
        }
        .accessibilityIdentifier("club-switcher")
    }
}
