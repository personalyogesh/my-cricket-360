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
    @State private var email = ""
    @State private var password = ""

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 20) {
                Text("My Cricket 360")
                    .font(.largeTitle.bold())
                Text("One account for Starks Cricket and CGI Steelers Cricket. Request membership to either or both clubs; each club’s admins approve independently.")
                    .foregroundStyle(.secondary)

                if SupabaseConfig.isConfigured {
                    TextField("Email", text: $email)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.emailAddress)
                    SecureField("Password", text: $password)
                    Button {
                        Task { await session.signInWithSupabase(email: email, password: password) }
                    } label: {
                        Text(session.isLoading ? "Signing in…" : "Sign in with Supabase")
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(session.isLoading || email.isEmpty || password.isEmpty)
                    Text("Using publishable config for project \(SupabaseConfig.projectName).")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    Button {
                        Task { await session.signInWithDevAccount() }
                    } label: {
                        Text(session.isLoading ? "Signing in…" : "Continue with local demo token")
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(session.isLoading)
                    Text("Supabase URL/anon key not set in Info.plist — local API dev tokens only.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if let statusMessage = session.statusMessage {
                    Text(statusMessage)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                Spacer()
            }
            .padding()
            .navigationTitle("Welcome")
        }
    }
}

struct MainTabView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Home", systemImage: "house.fill") }
            SponsorsView()
                .tabItem { Label("Sponsors", systemImage: "star.circle.fill") }
            MembershipsView()
                .tabItem { Label("Clubs", systemImage: "person.3.fill") }
        }
    }
}
