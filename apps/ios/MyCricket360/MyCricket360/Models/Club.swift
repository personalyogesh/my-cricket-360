import Foundation

/// Founding clubs — must stay aligned with web/API allowlist seeds.
enum ClubSlug: String, Codable, CaseIterable, Identifiable {
    case starks
    case steelers

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .starks: return "Starks Cricket"
        case .steelers: return "CGI Steelers Cricket"
        }
    }

    var shortName: String {
        switch self {
        case .starks: return "Starks"
        case .steelers: return "Steelers"
        }
    }

    var primaryDomain: String {
        switch self {
        case .starks: return "starksgroup.org"
        case .steelers: return "cgisteelerscricket.org"
        }
    }

    var organizationId: String {
        switch self {
        case .starks: return "00000000-0000-4000-8000-000000000001"
        case .steelers: return "00000000-0000-4000-8000-000000000002"
        }
    }

    var foundingSponsorName: String {
        switch self {
        case .starks: return "Hashtag India Cary"
        case .steelers: return "CGI"
        }
    }
}

enum MembershipStatus: String, Codable {
    case pending
    case approved
    case rejected
    case suspended
    case revoked
}

struct ClubMembership: Identifiable, Codable, Equatable {
    var id: String { "\(club.rawValue)-\(status.rawValue)-\(role)" }
    let club: ClubSlug
    var status: MembershipStatus
    var role: String = "member"
}
