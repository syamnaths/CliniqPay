// Loop platform profiles. The owner (or coder) picks one or more platforms at
// the start; loop-init.mjs uses the profile to shape the atlas, the proof
// ladder, product rules, release steps and the commands in AGENTS.md.
// A profile never chooses the stack: it only lists common options.

export const PLATFORMS = {
    web: {
        label: 'Web app / PWA (runs in a browser)',
        stacks: 'plain HTML/CSS/JS, React, Vue, Svelte, Next.js, Astro',
        entry: 'Open the site',
        unit: 'a screen or page',
        node: true,
        test: 'npm test (or the test command of the chosen web stack)',
        proof: ['static', 'unit', 'runtime (local server)', 'browser (Playwright: real clicks, storage, service worker)', 'device (phone browser check)'],
        visual: 'phone-width and desktop screenshots in a real browser',
        version: 'Bump `?v=` pins, the service-worker cache name and pinned tests together when a served file changes.',
        text: 'locale files (for example `locales/<lang>.json`)',
        rules: ['Works at phone width without horizontal scroll; keyboard and screen-reader basics.', 'Offline and slow-network behaviour stated when the app is a PWA.'],
        hotspots: 'app shell / entry HTML, service worker and cache names, shared translations, router',
        release: ['Build or bundle the site', 'Check it on a phone browser', 'Owner approves the deploy', 'Deploy to the host', 'Confirm the live version number'],
        questions: ['Hosting (static host, server, or both)', 'Browsers and phones to support', 'Offline needed or not']
    },
    android: {
        label: 'Android app (native)',
        stacks: 'Kotlin + Jetpack Compose, Kotlin + Views, Java',
        entry: 'Launch the app',
        unit: 'a screen',
        node: false,
        test: './gradlew test (unit) and ./gradlew connectedAndroidTest (on an emulator or device)',
        proof: ['static', 'unit (JVM tests)', 'runtime (emulator: instrumented / UI tests)', 'device (named Android phone)'],
        visual: 'emulator or device screenshots at phone size, light and dark',
        version: 'Bump `versionCode` and `versionName` for every build that leaves the machine.',
        text: '`res/values-<lang>/strings.xml`',
        rules: ['Ask for runtime permissions only when needed, with a plain reason.', 'Handle back navigation, rotation and process death without losing user input.', 'Never commit the signing keystore or its passwords.'],
        hotspots: 'Gradle build files, AndroidManifest.xml, navigation graph, shared strings, theme',
        release: ['Signed release build (owner keeps the keystore)', 'Internal testing track on Google Play', 'Device check on a real phone', 'Owner approves the rollout', 'Staged production rollout'],
        questions: ['Minimum Android version', 'Google Play account and app id', 'Phones and tablets, or phones only']
    },
    ios: {
        label: 'iPhone / iPad app (native)',
        stacks: 'Swift + SwiftUI, Swift + UIKit',
        entry: 'Launch the app',
        unit: 'a screen',
        node: false,
        test: 'xcodebuild test (or Product > Test in Xcode) on a simulator',
        proof: ['static', 'unit (XCTest)', 'runtime (simulator: UI tests)', 'device (named iPhone / iPad)'],
        visual: 'simulator or device screenshots at iPhone size, light and dark',
        version: 'Bump the build number (CFBundleVersion) for every upload; bump the marketing version for releases.',
        text: '`Localizable.strings` / String Catalog per language',
        rules: ['Ask for permissions only when needed, with a plain usage description.', 'Support Dynamic Type and VoiceOver basics.', 'Never commit certificates, provisioning profiles or App Store Connect keys.'],
        hotspots: 'Xcode project file, Info.plist, entitlements, shared strings, app entry point',
        release: ['Archive a signed build', 'TestFlight internal testing', 'Device check on a real iPhone', 'Owner approves App Store submission', 'Release after review'],
        questions: ['Minimum iOS version', 'Apple developer account and bundle id', 'iPhone only or iPad too']
    },
    mobile: {
        label: 'Mobile app for Android and iPhone (one codebase)',
        stacks: 'Flutter, React Native, Kotlin Multiplatform, .NET MAUI',
        entry: 'Launch the app',
        unit: 'a screen',
        node: false,
        test: 'the chosen stack\'s test command (for example flutter test or npm test)',
        proof: ['static', 'unit', 'runtime (Android emulator and iOS simulator)', 'device (one named Android phone and one named iPhone)'],
        visual: 'screenshots on both an Android emulator and an iOS simulator',
        version: 'Bump the app version and build number for both stores together.',
        text: 'the stack\'s localisation files (for example ARB files or JSON locales)',
        rules: ['Check every feature on both platforms before calling it delivered.', 'Platform differences (permissions, back button, notifications) are written into the map.', 'Never commit signing keys, keystores or store credentials.'],
        hotspots: 'app entry, navigation, shared translations, native project folders (android/, ios/), dependency lock file',
        release: ['Signed builds for both stores', 'Play internal testing and TestFlight', 'Device check on both platforms', 'Owner approves the rollout', 'Release on both stores'],
        questions: ['Minimum Android and iOS versions', 'Store accounts and app ids', 'Which stack (Flutter, React Native, other)']
    },
    desktop: {
        label: 'Desktop app (Mac, Windows or Linux)',
        stacks: 'Tauri, Electron, Swift (macOS), .NET / WinUI, Qt',
        entry: 'Launch the app',
        unit: 'a window or screen',
        node: false,
        test: 'the chosen stack\'s test command',
        proof: ['static', 'unit', 'runtime (app launched locally)', 'device (each target operating system)'],
        visual: 'window screenshots on each target operating system',
        version: 'Bump the app version for every build that leaves the machine; keep the auto-update feed in step.',
        text: 'the stack\'s localisation files',
        rules: ['Keyboard shortcuts and menus follow each operating system.', 'Files the app writes go to the proper user folders, never next to the app.', 'Code signing and notarisation secrets are never committed.'],
        hotspots: 'app entry, window and menu setup, auto-update, installer config, shared translations',
        release: ['Signed (and notarised) builds per OS', 'Install test on each OS', 'Owner approves the release', 'Publish installers / update feed'],
        questions: ['Which operating systems', 'Auto-update needed or not', 'Signing accounts (Apple, Windows)']
    },
    backend: {
        label: 'Backend / API / service',
        stacks: 'Node.js, Python (FastAPI, Django), Go, Java / Kotlin (Spring), Rust',
        entry: 'Call the API',
        unit: 'an endpoint or job',
        node: false,
        test: 'the chosen stack\'s test command (for example pytest, go test ./..., npm test)',
        proof: ['static', 'unit', 'runtime (local server: real HTTP calls and database)', 'staging (deployed test environment)'],
        visual: 'request and response examples instead of screenshots',
        version: 'Version the API; database changes go in numbered migrations with a rollback note.',
        text: 'message catalogues for any user-facing errors',
        rules: ['Validate every input; never trust the client.', 'Secrets come from the environment, never from the repository.', 'Every endpoint in the map lists its errors and limits.'],
        hotspots: 'routes, database schema and migrations, auth, shared config, API contract',
        release: ['Migrations reviewed', 'Deploy to staging and smoke test', 'Owner approves production', 'Deploy with a rollback plan', 'Check health and logs'],
        questions: ['Hosting and database', 'Who calls this API (web, mobile, partners)', 'Auth method and data privacy rules']
    },
    cli: {
        label: 'Command-line tool or library / package',
        stacks: 'Node.js, Python, Go, Rust',
        entry: 'Run the command',
        unit: 'a command or public function',
        node: false,
        test: 'the chosen stack\'s test command',
        proof: ['static', 'unit', 'runtime (real command runs on sample input)', 'device (each target operating system)'],
        visual: 'terminal output examples instead of screenshots',
        version: 'Follow semantic versioning; update the changelog with every release.',
        text: 'help text and messages (translate only if the brief asks)',
        rules: ['Clear --help, exit codes and error messages.', 'Never change a public command or function without a changelog entry.'],
        hotspots: 'argument parsing, public API surface, package manifest, changelog',
        release: ['Changelog and version bump', 'Install test from a clean folder', 'Owner approves publishing', 'Publish to the registry', 'Tag the release'],
        questions: ['Which registry (npm, PyPI, crates.io, binaries)', 'Operating systems to support', 'Licence']
    },
    other: {
        label: 'Other (game, browser extension, embedded, bot, ...)',
        stacks: 'decided with the owner',
        entry: 'Start',
        unit: 'a part of the product',
        node: false,
        test: 'the test command agreed for the chosen stack',
        proof: ['static', 'unit', 'runtime', 'device'],
        visual: 'screenshots or recordings that match how the product is used',
        version: 'Bump the version the platform uses for every build that leaves the machine.',
        text: 'the platform\'s localisation files',
        rules: ['Write the platform\'s own proof and release steps into .loop/platform.md before building the first feature.'],
        hotspots: 'entry point, shared config, shared translations',
        release: ['Build for the platform', 'Real-use check', 'Owner approves the release', 'Publish'],
        questions: ['What exactly is the platform', 'How users get the product', 'How we prove a feature works']
    }
};

const SHORT = { web: 'Web', android: 'Android', ios: 'iOS', mobile: 'Mobile', desktop: 'Desktop', backend: 'Backend', cli: 'CLI', other: 'Other' };
const GITIGNORE = {
    android: ['.gradle/', 'build/', 'local.properties', '*.keystore', '*.jks', 'captures/'],
    ios: ['DerivedData/', 'xcuserdata/', '*.p12', '*.mobileprovision', 'Pods/'],
    mobile: ['build/', '.dart_tool/', 'Pods/', '*.keystore', '*.jks', 'local.properties'],
    desktop: ['dist/', 'out/', 'target/'],
    backend: ['__pycache__/', '.venv/', 'dist/', 'target/'],
    cli: ['dist/', 'target/', '__pycache__/']
};

export const PLATFORM_IDS = Object.keys(PLATFORMS);
const ALIASES = { pwa: 'web', website: 'web', site: 'web', 'web-app': 'web', iphone: 'ios', ipad: 'ios', apple: 'ios', 'cross-platform': 'mobile', flutter: 'mobile', 'react-native': 'mobile', api: 'backend', server: 'backend', service: 'backend', library: 'cli', package: 'cli', mac: 'desktop', windows: 'desktop', linux: 'desktop' };

export function parsePlatforms(value) {
    if (!value || (Array.isArray(value) && !value.length)) return [];
    const list = (Array.isArray(value) ? value : String(value).split(/[,+/ ]+/)).map(v => String(v).trim().toLowerCase()).filter(Boolean);
    const ids = list.map(v => ALIASES[v] || v);
    const unknown = ids.filter(id => !PLATFORMS[id]);
    if (unknown.length) throw new Error(`Unknown platform: ${unknown.join(', ')}. Choose from: ${PLATFORM_IDS.join(', ')}.`);
    return [...new Set(ids)];
}

// Guess for --adopt only; the result is printed so the coder can correct it.
export function detectPlatforms(files) {
    const has = name => files.includes(name);
    const found = [];
    if (has('pubspec.yaml') || (has('android') && has('ios'))) found.push('mobile');
    else if (has('build.gradle') || has('build.gradle.kts') || has('settings.gradle') || has('settings.gradle.kts')) found.push('android');
    else if (files.some(f => f.endsWith('.xcodeproj') || f.endsWith('.xcworkspace')) || has('Package.swift')) found.push('ios');
    if (has('src-tauri') || has('electron-builder.yml')) found.push('desktop');
    if (has('index.html') || has('public') || has('vite.config.js') || has('vite.config.ts') || has('next.config.js')) found.push('web');
    if (!found.length && (has('go.mod') || has('pyproject.toml') || has('requirements.txt') || has('Cargo.toml'))) found.push('backend');
    return found.length ? found : ['other'];
}

// Merge the chosen profiles into one description for templates.
export function platformProfile(ids) {
    const profiles = ids.map(id => ({ id, ...PLATFORMS[id] }));
    const uniq = list => [...new Set(list)];
    const tag = (p, text) => (profiles.length > 1 ? `${SHORT[p.id]}: ${text}` : text);
    return {
        ids,
        label: profiles.map(p => p.label).join(' + '),
        entry: profiles.length === 1 ? profiles[0].entry : 'Open the product',
        node: profiles.some(p => p.node),
        stacks: profiles.map(p => `${p.label}: ${p.stacks}`),
        tests: profiles.map(p => `${p.label}: ${p.test}`),
        proof: profiles.map(p => `${p.label}: ${p.proof.join(' → ')}`),
        visual: uniq(profiles.map(p => p.visual)),
        version: uniq(profiles.map(p => p.version)),
        text: uniq(profiles.map(p => p.text)),
        rules: uniq(profiles.flatMap(p => p.rules)),
        hotspots: uniq(profiles.map(p => p.hotspots)).join('; '),
        release: profiles.flatMap(p => p.release.map(step => tag(p, step))),
        gitignore: uniq(profiles.flatMap(p => GITIGNORE[p.id] || [])),
        questions: uniq(profiles.flatMap(p => p.questions))
    };
}
