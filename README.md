# Minecraft Frame Bench

[![CI](https://github.com/fortunexbt/minecraft-frame-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/fortunexbt/minecraft-frame-bench/actions/workflows/ci.yml)

A small harness for repeatable measurements of the **real Minecraft Java client** on macOS. Developed during actual Apple Silicon shader comparisons. Active validation is ongoing; this is not a general benchmark suite or a claim about the fastest configuration.

The Java agent samples `System.nanoTime()` at the return of `Minecraft.renderFrame(boolean)`, with a `runTick(boolean)` fallback. It buffers timestamps, checks focus, and writes CSV after the capture. Minescript supplies timed camera pans and movement while recording actual positions and world ticks. An optional native Swift helper sends macOS input through existing Accessibility permission; it neither requests nor changes permissions.

## What the metric means

Intervals measure **CPU frame production, including frame limiting**. They do not measure GPU execution, displayed frames, input latency, or generated-frame performance. Average FPS is frame intervals divided by their measured elapsed time. A 1% low is 1000 divided by the mean milliseconds of the slowest 1% of intervals. Do not interpret an inverse percentile as that metric.

## The AFK trap is a hard gate

Scripted movement does not reset Minecraft's native input-idle timer. In the tested releases, the default AFK policy reduces the client to 30 FPS after one minute, even with a moving camera and a focused window.

Set Minecraft's inactive FPS policy to **Minimized** and restart. The agent checks the live client's policy and throttle reason before arming; it refuses `AFK` even when the client has not yet reached the timeout. Refusals produce a run-specific marker. `m4policy.pyj` provides a separate in-game runtime probe. Policy regression tests cover latent AFK, minimized windows, menus, and legitimate gameplay caps.

## Build

Tested sampler mappings: Minecraft 26.2 and 26.3, native Java 25. Control routes require a compatible Minescript 5 installation. Install Minecraft, Java, the loader and Minescript separately from their official sources. No game, shader, mod, world, credential or native runtime is distributed here.

Use the exact existing ASM 9.10.1 JAR from the launcher's game classpath. Its [Maven Central origin](https://repo.maven.apache.org/maven2/org/ow2/asm/asm/9.10.1/asm-9.10.1.jar) has SHA-256 `ed825d10ab1399c8c0cb669e688cf0c8c82629b4c8399b58352b68e92ca10fcb`. Fabric rejects a second copy on the classpath, even with identical bytes. The build embeds the existing file's absolute URL in the manifest, so build on the machine where the agent will run. ASM is a separate BSD-licensed dependency, not embedded in the agent or copied into the mods folder.

```sh
python3 build.py --jdk /absolute/path/to/jdk --asm /absolute/path/to/asm-9.10.1.jar
```

Keep `frame-agent.jar` and `frame-sink.jar` together. Add this JVM argument through your launcher, using your own absolute output directory:

```text
-javaagent:/absolute/path/to/build/frame-agent.jar=/absolute/path/to/game/minescript/bench-output
```

Copy `minescript/` scripts into your disposable instance's `.minecraft/minescript/` directory. Their default output is `.minecraft/minescript/bench-output`; an optional `MCBENCH_EVIDENCE` environment variable overrides it and must match the agent argument.

## Test

`build.py` compiles the agent and runs `tests/PolicyTest.java` (the AFK and throttle-policy guard) before packaging, so a successful build means the policy tests passed. CI runs the same build (minus the macOS-only input helper) on Linux with Temurin 25, plus `ruff` and a byte-compile of the Python scripts. Benchmarks themselves need a real Minecraft install and are not run in CI.

## Capture

Use disposable worlds with recorded seeds and normal ticking and AI. Use Creative for protected camera tests and explicitly label spectator flight. Warm the scene and shader first. Do not perform downloads, builds, browsing or recording during a capture. Check background CPU, memory pressure and swap activity before arming. Keep the control layer identical between compared runs.

In Minecraft chat:

```text
\m4policy
\m4pan unique-run-id 120 0 5 6000 clear
\m4move another-run-id 60 fly
```

For an automatic macOS environment gate and saved context, use the optional driver instead of entering a route directly:

```sh
python3 scripts/capture.py unique-run-id --game /absolute/path/to/.minecraft --seconds 120 --route pan
python3 scripts/summarize.py /absolute/path/to/.minecraft/minescript/bench-output unique-run-id
```

The driver requires one visible foreground client and two consecutive samples with at least 75% total CPU idle and no new swap-outs. Failed preflights remain recorded. `--min-idle` is configurable and recorded: a different machine may need a different threshold. Inspect the process samples as well; this gate cannot prove that all background interference is absent. The native typing helper assumes a US keyboard mapping.

Pan parameters are run ID, seconds, starting yaw, pitch, time of day, and weather. Movement modes are `walk`, `sprint`, `fly`, `swim` and `shuttle`. Movement starts at the current position and orientation; prepare and verify a clear route. `shuttle` alternates 4-second walking legs and 2.8-second sprinting legs, turning 180 degrees. It requires a verified clear path of at least 24 blocks. This is a controlled workload, not a movement bot.

Restore the same stopped-world snapshot before each fresh-terrain comparison. Never copy an active save, downgrade a world, or compare a fresh route against one generated by the preceding candidate. Record actual framebuffer size, settings, background state and route completion. Repeat and alternate candidate order. Keep invalid captures; do not silently drop unfavorable valid runs.

The summary script reads an evidence directory and run IDs. Reject loss of focus, any sampler error, truncated captures or incomplete routes. Tail metrics with inadequate sample size are unavailable. World-tick progression and `/tick query` support separate simulation checks; they are not GPU measurements.

Remove the agent and Minescript from a daily build and revalidate it through its ordinary launch path. The native helper's `release` command releases simulated movement keys. No helper creates a listener or startup service.

MIT-licensed harness source. Minecraft, ASM, Minescript, Java and shader projects retain their own licenses. This repository intentionally contains no private measurement data.
