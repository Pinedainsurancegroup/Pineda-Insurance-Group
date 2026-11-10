import SwiftUI
import AVKit
import PimflexCore

struct PlayerTrackChoice: Identifiable, Equatable {
    let id: Int
    let name: String
}

struct PlayerQualityChoice: Identifiable {
    let id: Int
    let name: String
    let bitRate: Double
}

@MainActor
final class PlaybackModel: ObservableObject {
    let player = AVPlayer()
    @Published var error: String?
    @Published var waiting = true
    @Published var playing = false
    @Published var seconds = 0.0
    @Published var duration = 0.0
    @Published var audioChoices: [PlayerTrackChoice] = []
    @Published var subtitleChoices: [PlayerTrackChoice] = []
    @Published var qualityChoices: [PlayerQualityChoice] = []
    @Published var selectedAudio = -2
    @Published var selectedSubtitle = -2
    @Published var selectedQuality = 0
    private var audioGroup: AVMediaSelectionGroup?
    private var subtitleGroup: AVMediaSelectionGroup?
    private var optionsTask: Task<Void, Never>?
    #if DEBUG
    private var preview = false
    #endif
    private var status: NSKeyValueObservation?
    private var timeControl: NSKeyValueObservation?
    private var timer: Any?
    private var end: NSObjectProtocol?
    private var fail: NSObjectProtocol?
    private var stalled: NSObjectProtocol?
    private var startTimeout: Task<Void, Never>?
    private var save: ((Double) -> Void)?
    private var lastSavedSeconds = 0.0
    private var ended = false

    func start(url: URL, resume: Double, save: @escaping (Double) -> Void) {
        stop(); self.save = save; waiting = true; error = nil
        do { try AVAudioSession.sharedInstance().setCategory(.playback, mode: .moviePlayback); try AVAudioSession.sharedInstance().setActive(true) }
        catch { self.error = "No se pudo activar el audio."; waiting = false; return }
        let item = AVPlayerItem(url: url)
        player.replaceCurrentItem(with: item)
        player.allowsExternalPlayback = true
        loadOptions(for: item)
        status = item.observe(\.status, options: [.initial, .new]) { [weak self] item, _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                if item.status == .failed {
                    self.waiting = false; self.error = "No se pudo reproducir. Comprueba el canal y su compatibilidad con iPhone."; self.startTimeout?.cancel()
                } else if item.status == .readyToPlay {
                    guard self.error == nil else { return }
                    self.waiting = true
                    let duration = item.duration.seconds
                    if resume > 5 && duration.isFinite && resume < duration - 10 {
                        await self.player.seek(to: CMTime(seconds: resume, preferredTimescale: 600))
                    }
                    if self.player.currentItem === item { self.player.play() }
                }
            }
        }
        timeControl = player.observe(\.timeControlStatus, options: [.new]) { [weak self] player, _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item, self.error == nil else { return }
                self.playing = player.timeControlStatus == .playing
                if player.timeControlStatus == .playing {
                    self.waiting = false; self.startTimeout?.cancel()
                } else if player.timeControlStatus == .waitingToPlayAtSpecifiedRate {
                    self.waiting = true; self.armTimeout(for: item)
                } else if player.timeControlStatus == .paused {
                    self.waiting = false; self.startTimeout?.cancel()
                }
            }
        }
        stalled = NotificationCenter.default.addObserver(forName: .AVPlayerItemPlaybackStalled, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item, self.error == nil else { return }
                self.waiting = true; self.armTimeout(for: item)
            }
        }
        timer = player.addPeriodicTimeObserver(forInterval: CMTime(seconds: 0.5, preferredTimescale: 600), queue: .main) { [weak self] time in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                self.seconds = time.seconds.isFinite ? max(0, time.seconds) : 0
                self.duration = item.duration.seconds.isFinite ? max(0, item.duration.seconds) : 0
                if !self.ended, abs(self.seconds - self.lastSavedSeconds) >= 10 { self.save?(self.seconds); self.lastSavedSeconds = self.seconds }
            }
        }
        end = NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                self.ended = true; self.playing = false; self.save?(0)
            }
        }
        fail = NotificationCenter.default.addObserver(forName: .AVPlayerItemFailedToPlayToEndTime, object: item, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.player.currentItem === item else { return }
                self.waiting = false; self.startTimeout?.cancel()
                self.error = "La transmisión se interrumpió. Intenta reproducirla de nuevo."
            }
        }
        armTimeout(for: item)
    }
    private func loadOptions(for item: AVPlayerItem) {
        optionsTask?.cancel()
        optionsTask = Task { [weak self] in
            let audio = try? await item.asset.loadMediaSelectionGroup(for: .audible)
            let subtitles = try? await item.asset.loadMediaSelectionGroup(for: .legible)
            let variants: [AVAssetVariant]
            if let asset = item.asset as? AVURLAsset { variants = (try? await asset.load(.variants)) ?? [] }
            else { variants = [] }
            guard let self, !Task.isCancelled, self.player.currentItem === item else { return }
            self.audioGroup = audio
            self.subtitleGroup = subtitles
            self.audioChoices = audio?.options.enumerated().map { PlayerTrackChoice(id: $0.offset, name: $0.element.displayName) } ?? []
            self.subtitleChoices = subtitles?.options.enumerated().map { PlayerTrackChoice(id: $0.offset, name: $0.element.displayName) } ?? []
            // These are upper bandwidth preferences, not a guarantee that AVPlayer
            // selects one exact rendition. Only advertise rates in this asset.
            let rates = Set(variants.compactMap(\.peakBitRate).filter { $0.isFinite && $0 > 0 }).sorted()
            self.qualityChoices = rates.count > 1 ? rates.enumerated().map {
                PlayerQualityChoice(id: $0.offset + 1, name: String(format: "Hasta %.2f Mb/s", $0.element / 1_000_000), bitRate: $0.element)
            } : []
        }
    }

    var canDisableSubtitles: Bool {
        #if DEBUG
        if preview { return true }
        #endif
        return subtitleGroup?.allowsEmptySelection == true
    }
    func selectAudio(_ id: Int) {
        #if DEBUG
        if preview { selectedAudio = id; return }
        #endif
        guard let item = player.currentItem, let group = audioGroup else { return }
        if id == -2 { item.selectMediaOptionAutomatically(in: group) }
        else if group.options.indices.contains(id) { item.select(group.options[id], in: group) }
        else { return }
        selectedAudio = id
    }
    func selectSubtitle(_ id: Int) {
        #if DEBUG
        if preview { selectedSubtitle = id; return }
        #endif
        guard let item = player.currentItem, let group = subtitleGroup else { return }
        if id == -2 { item.selectMediaOptionAutomatically(in: group) }
        else if id == -1, group.allowsEmptySelection { item.select(nil, in: group) }
        else if group.options.indices.contains(id) { item.select(group.options[id], in: group) }
        else { return }
        selectedSubtitle = id
    }
    func selectQuality(_ id: Int) {
        guard id == 0 || qualityChoices.contains(where: { $0.id == id }) else { return }
        player.currentItem?.preferredPeakBitRate = qualityChoices.first(where: { $0.id == id })?.bitRate ?? 0
        selectedQuality = id
    }
    func togglePause() {
        #if DEBUG
        if preview { playing.toggle(); return }
        #endif
        guard player.currentItem != nil, error == nil else { return }
        if player.rate != 0 { player.pause() }
        else if ended, let item = player.currentItem {
            ended = false; lastSavedSeconds = 0
            player.seek(to: .zero) { [weak self] _ in
                Task { @MainActor [weak self] in
                    guard let self, self.player.currentItem === item else { return }
                    self.player.play()
                }
            }
        } else { player.play() }
    }
    func seek(to value: Double) {
        guard value.isFinite, duration > 0 else { return }
        let target = min(max(0, value), max(0, duration - 0.5))
        #if DEBUG
        if preview { seconds = target; return }
        #endif
        ended = false
        player.seek(to: CMTime(seconds: target, preferredTimescale: 600))
    }
    #if DEBUG
    func showPreview() {
        stop(); preview = true; error = nil; waiting = false; playing = true; duration = 300
        audioChoices = [PlayerTrackChoice(id: 0, name: "Español"), PlayerTrackChoice(id: 1, name: "Inglés")]
        subtitleChoices = [PlayerTrackChoice(id: 0, name: "Español")]
        qualityChoices = [PlayerQualityChoice(id: 1, name: "Hasta 2.00 Mb/s", bitRate: 2_000_000),
                          PlayerQualityChoice(id: 2, name: "Hasta 5.00 Mb/s", bitRate: 5_000_000)]
    }
    #endif

    private func armTimeout(for item: AVPlayerItem) {
        startTimeout?.cancel()
        startTimeout = Task { [weak self] in
            do { try await Task.sleep(nanoseconds: 30_000_000_000) } catch { return }
            guard let self, self.waiting, self.player.currentItem === item else { return }
            self.player.pause(); self.waiting = false; self.error = "El canal tardó demasiado en responder. Intenta de nuevo."
        }
    }
    func stop() {
        optionsTask?.cancel(); optionsTask = nil
        audioGroup = nil; subtitleGroup = nil
        audioChoices = []; subtitleChoices = []; qualityChoices = []
        selectedAudio = -2; selectedSubtitle = -2; selectedQuality = 0
        playing = false; seconds = 0; duration = 0; lastSavedSeconds = 0
        #if DEBUG
        preview = false
        #endif
        if !ended { save?(player.currentTime().seconds) }
        ended = false; save = nil; player.pause()
        status = nil; timeControl = nil; startTimeout?.cancel(); startTimeout = nil
        if let timer { player.removeTimeObserver(timer) }; timer = nil
        for observer in [end, fail, stalled].compactMap({ $0 }) { NotificationCenter.default.removeObserver(observer) }
        end = nil; fail = nil; stalled = nil; player.replaceCurrentItem(with: nil)
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}

struct NativePlayer: UIViewControllerRepresentable {
    let player: AVPlayer
    var fill = false
    var playing = false
    var seconds = 0.0
    func makeUIViewController(context: Context) -> AVPlayerViewController {
        let controller = AVPlayerViewController()
        controller.player = player
        controller.showsPlaybackControls = false
        controller.videoGravity = fill ? .resizeAspectFill : .resizeAspect
        controller.view.isAccessibilityElement = true
        controller.view.accessibilityLabel = "Video"
        controller.view.accessibilityIdentifier = "nativeVideoSurface"
        // PiP intentionally disabled until lifecycle/device tests cover background dismissal.
        controller.allowsPictureInPicturePlayback = false
        return controller
    }
    func updateUIViewController(_ controller: AVPlayerViewController, context: Context) {
        controller.player = player
        controller.videoGravity = fill ? .resizeAspectFill : .resizeAspect
        controller.view.accessibilityValue = playing && seconds >= 1 ? "Reproduciendo" : "En pausa"
    }
    static func dismantleUIViewController(_ controller: AVPlayerViewController, coordinator: ()) { controller.player = nil }
}

struct PlayerScreen: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.accessibilityVoiceOverEnabled) private var voiceOverEnabled
    @StateObject private var playback = PlaybackModel()
    @StateObject private var compatible = CompatiblePlaybackModel()
    @State private var usesCompatible = false
    @State private var playbackAccount: Account?
    @State private var controlsVisible = true
    @State private var optionsVisible = false
    @State private var routePickerActive = false
    @State private var scrubbing = false
    @State private var scrubPosition = 0.0
    @State private var fill = false
    @State private var hideTask: Task<Void, Never>?
    let item: MediaItem

    private var waiting: Bool { usesCompatible ? compatible.waiting : playback.waiting }
    private var error: String? { usesCompatible ? compatible.error : playback.error }
    private var playing: Bool { usesCompatible ? compatible.playing : playback.playing }
    private var seconds: Double { usesCompatible ? compatible.seconds : playback.seconds }
    private var duration: Double { usesCompatible ? compatible.duration : playback.duration }
    private var canSeek: Bool { item.kind != .live && duration > 0 && (!usesCompatible || compatible.seekable) }
    private var preview: Bool {
        #if DEBUG
        return model.usesTestFixtures && !ProcessInfo.processInfo.arguments.contains("--test-mkv-playback") && !ProcessInfo.processInfo.arguments.contains("--test-native-playback")
        #else
        return false
        #endif
    }

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            if usesCompatible {
                CompatibleVideoSurface(playback: compatible).ignoresSafeArea()
            } else {
                NativePlayer(player: playback.player, fill: fill, playing: playback.playing, seconds: playback.seconds).ignoresSafeArea().allowsHitTesting(false)
            }
            if preview {
                Text("Vista previa · sin transmisión").foregroundStyle(.secondary).accessibilityIdentifier("playerFixture")
            }
            // The full-screen reveal target remains available while the chrome is hidden.
            Button(action: showControls) { Color.clear.contentShape(Rectangle()) }
                .buttonStyle(.plain).accessibilityLabel("Mostrar controles")
                .accessibilityIdentifier("playerRevealControls")
            if waiting {
                ProgressView("Abriendo transmisión…").tint(.white)
                    .accessibilityIdentifier("playbackWaiting").allowsHitTesting(false)
            }
            if let error {
                VStack(spacing: 20) {
                    Image(systemName: "exclamationmark.triangle").font(.largeTitle)
                    Text(error).multilineTextAlignment(.center)
                    Button("Reintentar") { start(forceCompatible: usesCompatible) }.buttonStyle(.borderedProminent).tint(.cyan).foregroundStyle(.black)
                    if !usesCompatible {
                        Button("Probar modo compatible") { start(forceCompatible: true) }.buttonStyle(.bordered)
                    }
                }.foregroundStyle(.white).padding(30).frame(maxWidth: .infinity, maxHeight: .infinity).background(.black.opacity(0.9))
            }
            if controlsVisible || error != nil {
                controls.accessibilityIdentifier("playerControls")
            }
        }.task { start() }
            .sheet(isPresented: $optionsVisible, onDismiss: showControls) { options }
            .onDisappear { hideTask?.cancel(); hideTask = nil; playback.stop(); compatible.stop() }
            .onChange(of: optionsVisible) { _ in scheduleHide() }
            .onChange(of: voiceOverEnabled) { _ in showControls() }
            .onChange(of: waiting) { _ in showControls() }
            .onChange(of: error) { _ in showControls() }
            .onChange(of: scenePhase) { phase in
                if phase == .background, model.account == playbackAccount {
                    if usesCompatible { compatible.savePosition() }
                    else { model.savePosition(playback.player.currentTime().seconds, item: item) }
                }
                if phase == .active { showControls() } else { hideTask?.cancel() }
            }
    }

    private var controls: some View {
        VStack {
            HStack {
                Button { dismiss() } label: { Label("Cerrar", systemImage: "xmark").padding(12) }
                    .background(.ultraThinMaterial, in: Capsule()).accessibilityIdentifier("playerClose")
                Spacer(minLength: 8)
                Text(item.name).font(.headline).lineLimit(1)
                Spacer(minLength: 8)
                Button { optionsVisible = true; showControls() } label: {
                    Image(systemName: "slider.horizontal.3").frame(width: 48, height: 48)
                }.accessibilityLabel("Audio, subtítulos y calidad").accessibilityIdentifier("playerOptions")
            }.padding(12).background(.black.opacity(0.6))
            Spacer()
            if error == nil {
                VStack(spacing: 12) {
                    if canSeek {
                        Slider(value: Binding(get: { scrubbing ? scrubPosition : min(seconds, max(1, duration)) }, set: { value in
                            scrubPosition = value
                            // VoiceOver adjustments do not always invoke onEditingChanged.
                            if !scrubbing { seek(value); showControls() }
                        }), in: 0...max(1, duration), onEditingChanged: { editing in
                            if editing { scrubPosition = seconds }
                            scrubbing = editing
                            if !editing { seek(scrubPosition) }
                            showControls()
                        }).accessibilityLabel("Posición del video").accessibilityIdentifier("playerTimeline")
                    }
                    HStack(spacing: 16) {
                        Text(clock(seconds)).monospacedDigit().font(.caption)
                            .accessibilityIdentifier("playbackPosition")
                        Spacer(minLength: 0)
                        if canSeek {
                            Button { seek(seconds - 10); showControls() } label: { Image(systemName: "gobackward.10").frame(width: 44, height: 44) }
                                .accessibilityLabel("Retroceder 10 segundos").accessibilityIdentifier("playerSeekBackward")
                        }
                        Button {
                            if usesCompatible { compatible.togglePause() } else { playback.togglePause() }
                            showControls()
                        } label: { Image(systemName: playing ? "pause.fill" : "play.fill").frame(width: 44, height: 44) }
                            .accessibilityLabel(playing ? "Pausar" : "Reproducir")
                            .accessibilityIdentifier(usesCompatible ? "compatiblePlayPause" : "playerPlayPause")
                        if canSeek {
                            Button { seek(seconds + 10); showControls() } label: { Image(systemName: "goforward.10").frame(width: 44, height: 44) }
                                .accessibilityLabel("Adelantar 10 segundos").accessibilityIdentifier("playerSeekForward")
                        }
                        Spacer(minLength: 0)
                        if item.kind == .live { Text("EN DIRECTO").font(.caption) }
                        else { Text(clock(duration)).monospacedDigit().font(.caption) }
                    }.font(.title3)
                    if !usesCompatible {
                        HStack {
                            Button { fill.toggle(); showControls() } label: {
                                Label(fill ? "Ajustar" : "Llenar", systemImage: "arrow.up.left.and.arrow.down.right")
                            }.accessibilityIdentifier("playerAspect")
                            Spacer()
                            PlayerAirPlayButton { active in
                                routePickerActive = active; showControls()
                            }.frame(width: 44, height: 44).accessibilityLabel("AirPlay")
                        }.font(.callout)
                    }
                }.padding(16).background(.black.opacity(0.75), in: RoundedRectangle(cornerRadius: 16)).padding(12)
            }
        }.foregroundStyle(.white).tint(.cyan).buttonStyle(.plain)
    }

    private var options: some View {
        NavigationStack {
            List {
                if preview { Text("Opciones ficticias para pruebas de interfaz; sin transmisión.").font(.footnote) }
                Section("Audio") {
                    let choices = usesCompatible ? compatible.audioChoices : playback.audioChoices
                    if choices.isEmpty { Text("Esta transmisión no ofrece pistas de audio seleccionables.") }
                    else {
                        if !usesCompatible {
                            optionRow("Automático", id: "playerAudio--2", selected: playback.selectedAudio == -2) { playback.selectAudio(-2) }
                        }
                        ForEach(choices) { choice in
                            optionRow(choice.name, id: "playerAudio-\(choice.id)", selected: (usesCompatible ? compatible.selectedAudio : playback.selectedAudio) == choice.id) {
                                if usesCompatible { compatible.selectAudio(choice.id) } else { playback.selectAudio(choice.id) }
                            }
                        }
                    }
                }
                Section("Subtítulos") {
                    let choices = usesCompatible ? compatible.subtitleChoices : playback.subtitleChoices
                    if choices.isEmpty { Text("Esta transmisión no ofrece subtítulos seleccionables.") }
                    else {
                        if !usesCompatible {
                            optionRow("Automático", id: "playerSubtitle--2", selected: playback.selectedSubtitle == -2) { playback.selectSubtitle(-2) }
                        }
                        if usesCompatible || playback.canDisableSubtitles {
                            optionRow("Desactivados", id: "playerSubtitle--1", selected: (usesCompatible ? compatible.selectedSubtitle : playback.selectedSubtitle) == -1) {
                                if usesCompatible { compatible.selectSubtitle(-1) } else { playback.selectSubtitle(-1) }
                            }
                        }
                        ForEach(choices.filter { $0.id >= 0 }) { choice in
                            optionRow(choice.name, id: "playerSubtitle-\(choice.id)", selected: (usesCompatible ? compatible.selectedSubtitle : playback.selectedSubtitle) == choice.id) {
                                if usesCompatible { compatible.selectSubtitle(choice.id) } else { playback.selectSubtitle(choice.id) }
                            }
                        }
                    }
                }
                Section("Calidad") {
                    if usesCompatible {
                        Text("El modo compatible gestiona la calidad de esta transmisión; no expone selección de variantes.")
                    } else if playback.qualityChoices.isEmpty {
                        Text("Automática. Esta transmisión no ofrece varias calidades seleccionables.")
                    } else {
                        optionRow("Automática", id: "playerQuality-0", selected: playback.selectedQuality == 0) { playback.selectQuality(0) }
                        ForEach(playback.qualityChoices) { choice in
                            optionRow(choice.name, id: "playerQuality-\(choice.id)", selected: playback.selectedQuality == choice.id) { playback.selectQuality(choice.id) }
                        }
                        Text("Preferencia de ancho de banda entre las variantes disponibles. El reproductor puede ajustar la calidad según la conexión.").font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }.navigationTitle("Reproducción").navigationBarTitleDisplayMode(.inline)
                .toolbar { Button("Listo") { optionsVisible = false }.accessibilityIdentifier("playerOptionsDone") }
        }
    }

    private func optionRow(_ name: String, id: String, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack { Text(name); Spacer(); if selected { Image(systemName: "checkmark") } }
        }.accessibilityIdentifier(id).accessibilityValue(selected ? "Seleccionado" : "No seleccionado")
    }
    private func clock(_ value: Double) -> String {
        let total = Int(max(0, min(value.isFinite ? value : 0, Double(Int32.max))))
        return total >= 3600 ? String(format: "%d:%02d:%02d", total / 3600, total / 60 % 60, total % 60) : String(format: "%d:%02d", total / 60, total % 60)
    }
    private func seek(_ value: Double) {
        if usesCompatible { compatible.seek(to: value) } else { playback.seek(to: value) }
    }
    private func showControls() { controlsVisible = true; scheduleHide() }
    private func scheduleHide() {
        hideTask?.cancel(); hideTask = nil
        guard scenePhase == .active, !optionsVisible, !routePickerActive, !scrubbing, !voiceOverEnabled, !waiting, error == nil else { return }
        hideTask = Task { @MainActor in
            do { try await Task.sleep(nanoseconds: 4_000_000_000) } catch { return }
            guard !Task.isCancelled else { return }
            controlsVisible = false
        }
    }
    private func start(forceCompatible: Bool = false) {
        guard let account = model.account else { return }
        playbackAccount = account
        #if DEBUG
        if preview {
            compatible.stop(); usesCompatible = false; playback.showPreview(); showControls(); return
        }
        #endif
        do {
            let url: URL
            #if DEBUG
            if model.usesTestFixtures, ProcessInfo.processInfo.arguments.contains("--test-mkv-playback") {
                guard let fixture = Bundle.main.url(forResource: "PlaybackFixture", withExtension: "mkv") else { throw PimflexError.invalidResponse }
                url = fixture
            } else if model.usesTestFixtures, ProcessInfo.processInfo.arguments.contains("--test-native-playback") {
                guard let fixture = Bundle.main.url(forResource: "PlaybackFixture", withExtension: "mp4") else { throw PimflexError.invalidResponse }
                url = fixture
            } else { url = try Endpoint.playback(account, item: item) }
            #else
            url = try Endpoint.playback(account, item: item)
            #endif
            playback.stop(); compatible.stop()
            usesCompatible = forceCompatible || PlaybackEngine.forMediaURL(url) == .compatible
            let save: (Double) -> Void = {
                guard model.account == account else { return }
                model.savePosition($0, item: item)
            }
            if usesCompatible { compatible.start(url: url, resume: model.positions[item.id] ?? 0, save: save) }
            else { playback.start(url: url, resume: model.positions[item.id] ?? 0, save: save) }
        } catch {
            playback.waiting = false; compatible.waiting = false
            if usesCompatible { compatible.error = model.message(error) }
            else { playback.error = model.message(error) }
        }
        showControls()
    }
}

private struct PlayerAirPlayButton: UIViewRepresentable {
    let presenting: (Bool) -> Void
    final class Coordinator: NSObject, AVRoutePickerViewDelegate {
        var presenting: (Bool) -> Void
        init(presenting: @escaping (Bool) -> Void) { self.presenting = presenting }
        func routePickerViewWillBeginPresentingRoutes(_ routePickerView: AVRoutePickerView) { presenting(true) }
        func routePickerViewDidEndPresentingRoutes(_ routePickerView: AVRoutePickerView) { presenting(false) }
    }
    func makeCoordinator() -> Coordinator { Coordinator(presenting: presenting) }
    func makeUIView(context: Context) -> AVRoutePickerView {
        let view = AVRoutePickerView()
        view.tintColor = .white; view.activeTintColor = .cyan
        view.prioritizesVideoDevices = true; view.delegate = context.coordinator
        return view
    }
    func updateUIView(_ view: AVRoutePickerView, context: Context) { context.coordinator.presenting = presenting }
}
