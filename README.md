# Minecraft Frame Bench

[![CI](https://github.com/fortunexbt/minecraft-frame-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/fortunexbt/minecraft-frame-bench/actions/workflows/ci.yml)

A harness for measuring frame times of the real Minecraft Java client on macOS, built to compare shader and settings configurations on Apple Silicon. A Java agent timestamps each frame the client produces, Minescript drives a timed camera pan or movement route, and a summary script turns the capture into FPS, percentiles and stall counts.

## Build

You need Java 25, a Minecraft instance with Minescript 5, and the ASM 9.10.1 JAR already on the launcher's game classpath. The sampler was tested on Minecraft 26.2 and 26.3.

```sh
python3 build.py --jdk /path/to/jdk-25 --asm /path/to/asm-9.10.1.jar
```

`build.py` checks the JAR against the [Maven Central release](https://repo.maven.apache.org/maven2/org/ow2/asm/asm/9.10.1/asm-9.10.1.jar) (SHA-256 `ed825d10ab1399c8c0cb669e688cf0c8c82629b4c8399b58352b68e92ca10fcb`), runs the policy tests in `tests/PolicyTest.java` and writes `build/frame-agent.jar` and `build/frame-sink.jar`. On macOS it also builds `build/controller`, an optional input helper. Fabric rejects a second copy of ASM even with identical bytes, so the agent points at the launcher's own file by absolute path. Build on the machine that runs the game.

Keep the two JARs together and add the agent to the launcher's JVM arguments, pointing at the directory the scripts write to.

```text
-javaagent:/path/to/build/frame-agent.jar=/path/to/.minecraft/minescript/bench-output
```

Copy `minescript/` into the instance's `.minecraft/minescript/`. To write somewhere other than `bench-output`, set `MCBENCH_EVIDENCE` to the same path as the agent argument.

## AFK policy

Scripted movement doesn't reset Minecraft's input-idle timer, and in the tested releases the default AFK policy drops the client to 30 FPS after a minute even with the camera moving. Set the inactive FPS policy to Minimized and restart. Before each capture the agent reads the live client's policy and throttle reason, and refuses to record under AFK or any active throttle. `\m4policy` prints those values in chat.

## Capture

Type these in Minecraft chat, each with a run ID that hasn't been used before.

```text
\m4pan run-01 120 0 5 6000 clear
\m4move run-02 60 fly
```

`m4pan` takes seconds, starting yaw, pitch, time of day and weather, and pans 90 degrees out and back from a fixed spot. `m4move` holds forward in `walk`, `sprint`, `fly`, `swim` or `shuttle` mode from the current position, so check the route is clear first.

The optional driver adds an environment gate and records context. It needs `build/controller` with Accessibility permission and a US keyboard layout.

```sh
python3 scripts/capture.py run-03 --game /path/to/.minecraft --seconds 120 --route pan
python3 scripts/summarize.py /path/to/.minecraft/minescript/bench-output run-03
```

`capture.py` refuses unless exactly one Minecraft window is in front and the last two of three `top` samples show at least 75% CPU idle (`--min-idle`) and no new swap-outs. Refused runs keep their records. It saves the `top` output, mod hashes and shader settings next to the capture, then types the route command into chat.

The [capture protocol](docs/capture-protocol.md) covers world setup, comparisons and cleanup.

## Results

`summarize.py` writes `<run-id>-summary.json` with average FPS, median, p95 and p99 frame time, 1% low, time over the 60 and 90 FPS budgets and stall counts at 33, 50 and 100 ms. p99.9 and the 0.1% low appear only with at least 10,000 intervals. A run is invalid if focus was lost, the sampler failed or filled its buffer, the policy check is missing or the route didn't finish.

The intervals measure CPU frame production, including the frame limiter. They don't measure GPU execution, displayed frames, input latency or generated frames. Average FPS is the number of intervals divided by their total time. The 1% low is 1000 divided by the mean of the slowest 1% of intervals in milliseconds, not an inverse percentile.

CI builds the agent and runs the policy tests on Linux with Temurin 25, then lints and byte-compiles the Python. Captures need a real game and don't run in CI.

## Licence

The harness source is MIT licensed. Minecraft, ASM (BSD), Minescript, Java and shader projects keep their own licences, and no game, shader, mod, world, credential or measurement data is distributed here. The input helper uses only Accessibility permission you've already granted, refuses to send input unless Minecraft or Prism Launcher is in front, and creates no listener or startup service.
