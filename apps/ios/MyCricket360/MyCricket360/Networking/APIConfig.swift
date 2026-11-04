import Foundation

enum APIConfig {
    /// Override via Info.plist `MC360APIBaseURL` when needed.
    static var baseURL: URL {
        if let raw = Bundle.main.object(forInfoDictionaryKey: "MC360APIBaseURL") as? String,
           let url = URL(string: raw) {
            return url
        }
        return URL(string: "http://127.0.0.1:8400")!
    }
}
