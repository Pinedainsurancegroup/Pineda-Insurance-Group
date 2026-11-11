import SwiftUI
import AVKit
import PimflexCore

func playbackClock(_ value: Double) -> String {
    let total = Int(max(0, min(value.isFinite ? value : 0, Double(Int32.max))))
    return total >= 3600 ? String(format: "%d:%02d:%02d", total / 3600, total / 60 % 60, total % 60) : String(format: "%d:%02d", total / 60, total % 60)
}

struct PlayerTrackChoice: Identifiable, Equatable {
    let id: Int
    let name: String
}

struct PlayerQualityChoice: Identifiable {
    let id: Int
    let name: String
    let bitRate: Double
}

enum PlayerOptionSection: CaseIterable, Hashable { case audio, subtitles, quality }
enum PlayerOptionLoadState: Equatable { case loading, loaded, failed }

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
    @Published private(set) var audioOptionsState: PlayerOptionLoadState = .loading
    @Published private(set) var subtitleOptionsState: PlayerOptionLoadState = .loading
    @Published private(set) var qualityOptionsState: PlayerOptionLoadState = .loading
    private var audioGroup: AVMediaSelectionGroup?
    private var subtitleGroup: AVMediaSelectionGroup?
    private var optionsTasks: [PlayerOptionSection: Task<Void, Never>] = [:]
    #if DEBUG
    private var preview = false
    private var inspectTrackSelection = false
    @Published private(set) var actualTrackSelection = "audio=unknown;subtitle=unknown"
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
        #if DEBUG
        inspectTrackSelection = url.isFileURL && url.lastPathComponent == "TrackSelectionFixture.mp4"
            && ProcessInfo.processInfo.arguments.contains("--test-track-selection")
        #endif
        for section in PlayerOptionSection.allCases { loadOptions(section, for: item) }
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
                #if DEBUG
                self.updateTrackSelectionSnapshot()
                #endif
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
    func retryOptions(_ section: PlayerOptionSection) {
        guard let item = player.currentItem, optionsState(section) == .failed else { return }
        loadOptions(section, for: item)
    }
    private func optionsState(_ section: PlayerOptionSection) -> PlayerOptionLoadState {
        switch section {
        case .audio: return audioOptionsState
        case .subtitles: return subtitleOptionsState
        case .quality: return qualityOptionsState
        }
    }
    private func setOptionsState(_ state: PlayerOptionLoadState, for section: PlayerOptionSection) {
        switch section {
        case .audio: audioOptionsState = state
        case .subtitles: subtitleOptionsState = state
        case .quality: qualityOptionsState = state
        }
    }
    private func loadOptions(_ section: PlayerOptionSection, for item: AVPlayerItem) {
        optionsTasks[section]?.cancel()
        setOptionsState(.loading, for: section)
        // Independent tasks publish available tracks without waiting for variant metadata.
        optionsTasks[section] = Task { [weak self] in
            do {
                switch section {
                case .audio, .subtitles:
                    let group = try await item.asset.loadMediaSelectionGroup(for: section == .audio ? .audible : .legible)
                    guard let self, !Task.isCancelled, self.player.currentItem === item else { return }
                    let choices = group?.options.enumerated().map { PlayerTrackChoice(id: $0.offset, name: $0.element.displayName) } ?? []
                    let current = group.flatMap { item.currentMediaSelection.selectedMediaOption(in: $0) }
                    let selectedIndex = current.flatMap { group?.options.firstIndex(of: $0) }
                    if section == .audio {
                        self.audioGroup = group; self.audioChoices = choices
                        if self.selectedAudio >= 0 { self.selectedAudio = selectedIndex ?? -2 }
                    } else {
                        self.subtitleGroup = group; self.subtitleChoices = choices
                        if self.selectedSubtitle >= 0 { self.selectedSubtitle = selectedIndex ?? -2 }
                    }
                    self.setOptionsState(.loaded, for: section)
                case .quality:
                    let variants: [AVAssetVariant]
                    if let asset = item.asset as? AVURLAsset { variants = try await asset.load(.variants) }
                    else { variants = [] }
                    guard let self, !Task.isCancelled, self.player.currentItem === item else { return }
                    // Upper bandwidth preferences, not a guarantee of one exact rendition.
                    let rates = Set(variants.compactMap(\.peakBitRate).filter { $0.isFinite && $0 > 0 }).sorted()
                    let preferredRate = item.preferredPeakBitRate
                    self.qualityChoices = rates.count > 1 ? rates.enumerated().map {
                        PlayerQualityChoice(id: $0.offset + 1, name: String(format: "Hasta %.2f Mb/s", $0.element / 1_000_000), bitRate: $0.element)
                    } : []
                    self.selectedQuality = self.qualityChoices.first(where: { $0.bitRate == preferredRate })?.id ?? 0
                    self.setOptionsState(.loaded, for: section)
                }
            } catch {
                guard let self, !Task.isCancelled, self.player.currentItem === item else { return }
                self.setOptionsState(.failed, for: section)
            }
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
        player.seek(to: CMTime(seconds: target, preferredTimescale: 600),
                    toleranceBefore: .zero, toleranceAfter: .zero)
    }
    #if DEBUG
    private func updateTrackSelectionSnapshot() {
        guard inspectTrackSelection, let item = player.currentItem else { return }
        func language(in group: AVMediaSelectionGroup?) -> String {
            guard let group else { return "unknown" }
            guard let option = item.currentMediaSelection.selectedMediaOption(in: group) else { return "off" }
            let language = (option.extendedLanguageTag ?? option.locale?.languageCode ?? "unknown")
                .lowercased().split(separator: "-").first.map(String.init) ?? "unknown"
            switch language {
            case "es", "spa": return "spa"
            case "en", "eng": return "eng"
            default: return language
            }
        }
        let value = "audio=\(language(in: audioGroup));subtitle=\(language(in: subtitleGroup))"
        if actualTrackSelection != value { actualTrackSelection = value }
    }
    func showPreview() {
        stop(); preview = true; error = nil; waiting = false; playing = true; duration = 300
        audioChoices = [PlayerTrackChoice(id: 0, name: "Español"), PlayerTrackChoice(id: 1, name: "Inglés")]
        subtitleChoices = [PlayerTrackChoice(id: 0, name: "Español")]
        qualityChoices = [PlayerQualityChoice(id: 1, name: "Hasta 2.00 Mb/s", bitRate: 2_000_000),
                          PlayerQualityChoice(id: 2, name: "Hasta 5.00 Mb/s", bitRate: 5_000_000)]
        audioOptionsState = .loaded; subtitleOptionsState = .loaded; qualityOptionsState = .loaded
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
        for task in optionsTasks.values { task.cancel() }; optionsTasks = [:]
        audioGroup = nil; subtitleGroup = nil
        audioChoices = []; subtitleChoices = []; qualityChoices = []
        audioOptionsState = .loading; subtitleOptionsState = .loading; qualityOptionsState = .loading
        selectedAudio = -2; selectedSubtitle = -2; selectedQuality = 0
        playing = false; seconds = 0; duration = 0; lastSavedSeconds = 0
        #if DEBUG
        preview = false; inspectTrackSelection = false
        actualTrackSelection = "audio=unknown;subtitle=unknown"
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
        controller.view.accessibilityTraits.insert(.updatesFrequently)
        // PiP intentionally disabled until lifecycle/device tests cover background dismissal.
        controller.allowsPictureInPicturePlayback = false
        return controller
    }
    func updateUIViewController(_ controller: AVPlayerViewController, context: Context) {
        controller.player = player
        controller.videoGravity = fill ? .resizeAspectFill : .resizeAspect
        let state = playing && seconds >= 1 ? "Reproduciendo" : "En pausa"
        controller.view.accessibilityValue = "\(state) · \(playbackClock(seconds))"
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
        return model.usesTestFixtures && !ProcessInfo.processInfo.arguments.contains("--test-mkv-playback")
            && !ProcessInfo.processInfo.arguments.contains("--test-native-playback")
            && !ProcessInfo.processInfo.arguments.contains("--test-track-selection")
        #else
        return false
        #endif
    }
    #if DEBUG
    private var trackSelectionFixture: Bool {
        let arguments = ProcessInfo.processInfo.arguments
        return model.usesTestFixtures && arguments.contains("--test-track-selection")
            && !arguments.contains("--test-mkv-playback") && !arguments.contains("--test-native-playback")
    }
    #endif

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
                controls
            }
        }.task { start() }
            .sheet(isPresented: $optionsVisible, onDismiss: showControls) { options }
            .onDisappear { hideTask?.cancel(); hideTask = nil; playback.stop(); compatible.stop() }
            .onChange(of: optionsVisible) { _ in scheduleHide() }
            .onChange(of: voiceOverEnabled) { _ in showControls() }
            .onChange(of: waiting) { waiting in
                if !waiting, optionsVisible, usesCompatible { compatible.refreshTracks() }
                showControls()
            }
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
                Button {
                    if usesCompatible { compatible.refreshTracks() }
                    optionsVisible = true; showControls()
                } label: {
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
                        Text(playbackClock(seconds)).monospacedDigit().font(.caption)
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
                        else { Text(playbackClock(duration)).monospacedDigit().font(.caption) }
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
                    if !usesCompatible, playback.audioOptionsState != .loaded {
                        optionLoadStatus(playback.audioOptionsState, section: .audio, name: "audio", identifier: "playerAudioLoad")
                    } else if choices.isEmpty { Text("Esta transmisión no ofrece pistas de audio seleccionables.") }
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
                    if !usesCompatible, playback.subtitleOptionsState != .loaded {
                        optionLoadStatus(playback.subtitleOptionsState, section: .subtitles, name: "subtítulos", identifier: "playerSubtitleLoad")
                    } else if choices.isEmpty { Text("Esta transmisión no ofrece subtítulos seleccionables.") }
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
                    } else if playback.qualityOptionsState != .loaded {
                        optionLoadStatus(playback.qualityOptionsState, section: .quality, name: "calidad", identifier: "playerQualityLoad")
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
            }
            #if DEBUG
            // Keep the real-engine diagnostic outside List's virtualized rows.
            // Scrolling to the final subtitle must not remove the observed value.
            .safeAreaInset(edge: .top, spacing: 0) {
                if trackSelectionFixture, !usesCompatible {
                    Text("Selección nativa del archivo de prueba")
                        .font(.footnote).foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading).padding(12)
                        .accessibilityIdentifier("nativeTrackSelection")
                        .accessibilityValue(playback.actualTrackSelection)
                }
            }
            #endif
                .navigationTitle("Reproducción").navigationBarTitleDisplayMode(.inline)
                .toolbar { Button("Listo") { optionsVisible = false }.accessibilityIdentifier("playerOptionsDone") }
        }
    }

    @ViewBuilder
    private func optionLoadStatus(_ state: PlayerOptionLoadState, section: PlayerOptionSection, name: String, identifier: String) -> some View {
        if state == .loading {
            ProgressView("Cargando opciones de \(name)…").accessibilityIdentifier(identifier)
        } else if state == .failed {
            Text("No se pudieron cargar las opciones de \(name).")
            Button("Reintentar \(name)") { playback.retryOptions(section) }
                .accessibilityIdentifier(identifier + "Retry")
        }
    }
    private func optionRow(_ name: String, id: String, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack { Text(name); Spacer(); if selected { Image(systemName: "checkmark") } }
        }.accessibilityIdentifier(id).accessibilityValue(selected ? "Seleccionado" : "No seleccionado")
    }
    private func seek(_ value: Double) {
        if usesCompatible { compatible.seek(to: value) } else { playback.seek(to: value) }
    }
    private func showControls() { controlsVisible = true; scheduleHide() }
    private func scheduleHide() {
        hideTask?.cancel(); hideTask = nil
        #if DEBUG
        // Decoder integration tests need stable targets when XCTest input
        // delivery exceeds four seconds. Inactivity tests omit this flag.
        let arguments = ProcessInfo.processInfo.arguments
        if model.usesTestFixtures, arguments.contains("--keep-playback-controls-visible"),
           arguments.contains("--test-mkv-playback") || arguments.contains("--test-native-playback")
            || arguments.contains("--test-track-selection") { return }
        #endif
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
            } else if model.usesTestFixtures, ProcessInfo.processInfo.arguments.contains("--test-track-selection") {
                guard let fixture = Bundle.main.url(forResource: "TrackSelectionFixture", withExtension: "mp4") else { throw PimflexError.invalidResponse }
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
