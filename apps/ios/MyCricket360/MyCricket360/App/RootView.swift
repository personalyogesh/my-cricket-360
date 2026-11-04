import SwiftUI

struct RootView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        Group {
            if session.isSignedIn {
                MainTabView()
            } else {
                WelcomeView()
            }
        }
    }
}

struct WelcomeView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 20) {
                Text("My Cricket 360")
                    .font(.largeTitle.bold())
                Text("One account for Starks Cricket and CGI Steelers Cricket. Request membership to either or both clubs; each club’s admins approve independently.")
                    .foregroundStyle(.secondary)
                Button("Continue with demo account") {
                    session.signInDemo()
                }
                .buttonStyle(.borderedProminent)
                Spacer()
            }
            .padding()
            .navigationTitle("Welcome")
        }
    }
}

struct MainTabView: View {
    @EnvironmentObject private var session: AppSession

    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Home", systemImage: "house.fill") }
            SponsorsView()
                .tabItem { Label("Sponsors", systemImage: "star.circle.fill") }
            MembershipsView()
                .tabItem { Label("Clubs", systemImage: "person.3.fill") }
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                ClubSwitcher()
            }
        }
    }
}
