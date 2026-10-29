import SwiftUI
import AVKit
import PimflexCore

@MainActor
final class PlaybackModel: ObservableObject {
    let player = AVPlayer()
    @Published var error: String?
    @Published var waiting = true
    private var status: NSKeyValueObservation?
    private var timer: Any?
    private var end: NSObjectProtocol?
    private var fail: NSObjectProtocol?
    private var stalled: NSObjectProtocol?
    private var startTimeout: Task<Void, Never>?
    private var save: ((Double) -> Void)?

    func start(url: URL, resume: Double, save: @escaping (Double) -> Void) {
        stop(); self.save = save; waiting = true; error = nil
        do { try AVAudioSession.sharedInstance().setCategory(.playback, mode: .moviePlayback); try AVAudioSession.sharedInstance().setActive(true) }
        catch { self.error = "No se pudo activar el audio."; waiting = false; return }
        let item = AVPlayerItem(url: url)
        player.replaceCurrentItem(with: item)
        player.allowsExternalPlayback = true
        status = item.observe(\.status, options: [.initial, .new]) { [weak self] item, _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                if item.status == .failed {
                    self.waiting = false; self.error = "No se pudo reproducir. Comprueba el canal y su compatibilidad con iPhone."; self.startTimeout?.cancel()
                } else if item.status == .readyToPlay {
                    guard self.error == nil else { return }
                    self.waiting = false; self.startTimeout?.cancel()
                    let duration = item.duration.seconds
                    if resume > 5 && duration.isFinite && resume < duration - 10 {
                        await self.player.seek(to: CMTime(seconds: resume, preferredTimescale: 600))
                    }
                    if self.player.currentItem === item { self.player.play() }
                }
            }
        }
        timer = player.addPeriodicTimeObserver(forInterval: CMTime(seconds: 10, preferredTimescale: 1), queue: .main) { time in
            Task { @MainActor [weak self] in self?.save?(time.seconds) }
        }
        end = NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in self?.save?(0); self?.save = nil }
        }
        fail = NotificationCenter.default.addObserver(forName: .AVPlayerItemFailedToPlayToEndTime, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in self?.error = "La transmisión se interrumpió. Intenta reproducirla de nuevo." }
        }
        startTimeout = Task { [weak self] in
            do { try await Task.sleep(nanoseconds: 30_000_000_000) } catch { return }
            guard let self, self.waiting else { return }
            self.player.pause(); self.waiting = false; self.error = "El canal tardó demasiado en responder. Intenta de nuevo."
        }
    }
    func stop() {
        save?(player.currentTime().seconds); save = nil; player.pause()
        status = nil; startTimeout?.cancel(); startTimeout = nil
        if let timer { player.removeTimeObserver(timer) }; timer = nil
        for observer in [end, fail, stalled].compactMap({ $0 }) { NotificationCenter.default.removeObserver(observer) }
        end = nil; fail = nil; stalled = nil; player.replaceCurrentItem(with: nil)
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}

struct NativePlayer: UIViewControllerRepresentable {
    let player: AVPlayer
    func makeUIViewController(context: Context) -> AVPlayerViewController {
        let controller = AVPlayerViewController()
        controller.player = player
        // PiP intentionally disabled until lifecycle/device tests cover background dismissal.
        controller.allowsPictureInPicturePlayback = false
        return controller
    }
    func updateUIViewController(_ controller: AVPlayerViewController, context: Context) { controller.player = player }
    static func dismantleUIViewController(_ controller: AVPlayerViewController, coordinator: ()) { controller.player = nil }
}

struct PlayerScreen: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var playback = PlaybackModel()
    let item: MediaItem
    var body: some View {
        ZStack(alignment: .topLeading) {
            Color.black.ignoresSafeArea()
            NativePlayer(player: playback.player).ignoresSafeArea()
            if playback.waiting { ProgressView("Abriendo transmisión…").frame(maxWidth: .infinity, maxHeight: .infinity) }
            if let error = playback.error {
                VStack(spacing: 20) {
                    Image(systemName: "exclamationmark.triangle").font(.largeTitle)
                    Text(error).multilineTextAlignment(.center)
                    Button("Reintentar") { start() }.buttonStyle(.borderedProminent)
                }.padding(30).frame(maxWidth: .infinity, maxHeight: .infinity).background(.black.opacity(0.9))
            }
            Button { dismiss() } label: { Label("Cerrar", systemImage: "xmark").padding(12).background(.ultraThinMaterial, in: Capsule()) }.padding(16)
        }.task { start() }
            .onDisappear { playback.stop() }
            .onChange(of: scenePhase) { phase in
                if phase == .background { model.savePosition(playback.player.currentTime().seconds, item: item) }
            }
    }
    private func start() {
        guard let account = model.account else { return }
        do {
            let url = try Endpoint.playback(account, item: item)
            playback.start(url: url, resume: model.positions[item.id] ?? 0) { model.savePosition($0, item: item) }
        } catch { playback.waiting = false; playback.error = model.message(error) }
    }
}
