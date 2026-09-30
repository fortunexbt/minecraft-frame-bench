import csv, json, math, pathlib, statistics, sys

if len(sys.argv)<3: raise SystemExit('usage: summarize.py EVIDENCE RUN_ID [RUN_ID ...]')
root = pathlib.Path(sys.argv[1]).resolve()
for run in sys.argv[2:]:
    with (root / (run + '-frames.csv')).open() as f:
        values = [int(row['interval_ns']) / 1e6 for row in csv.DictReader(f) if int(row['interval_ns']) > 0]
    values.sort()
    def percentile(q):
        return values[min(len(values)-1, math.ceil(q*len(values))-1)]
    done = (root / (run + '-done.txt')).read_text()
    route_file = root / (run + '-route.json')
    route = json.loads(route_file.read_text()) if route_file.exists() else None
    start_file=root/(run+'-start.txt')
    start=start_file.read_text() if start_file.exists() else ''
    invalid=[]
    if 'live_inactivity_policy=MINIMIZED' not in start or 'live_throttle_reason=NONE' not in start:invalid.append('missing safe live-policy preflight')
    if 'unfocused_frames=0\n' not in done:invalid.append('lost focus or missing focus check')
    if 'frame_sink_error=\n' not in done or 'buffer_full=false' not in done:invalid.append('sampler error, truncation, or missing sampler status')
    if not route:invalid.append('route did not finish')
    result = dict(run=run, frame_intervals=len(values), seconds=sum(values)/1000,
        average_fps=1000/statistics.mean(values), median_ms=statistics.median(values),
        p95_ms=percentile(.95), p99_ms=percentile(.99),
        p999_ms=percentile(.999) if len(values)>=10000 else None,
        one_percent_low=1000/statistics.mean(values[-math.ceil(len(values)*.01):]),
        point_one_percent_low=1000/statistics.mean(values[-math.ceil(len(values)*.001):]) if len(values)>=10000 else None,
        time_over_16_667ms=sum(v for v in values if v>1000/60)/1000,
        time_over_11_111ms=sum(v for v in values if v>1000/90)/1000,
        stalls_33ms=sum(v>33.3 for v in values), stalls_50ms=sum(v>50 for v in values),
        stalls_100ms=sum(v>100 for v in values), sampler=done.strip(),
        route_complete=bool(route), valid=not invalid, invalid_reasons=invalid,
        metric='CPU frame-production intervals; includes frame limiter; not GPU presentation latency')
    (root / (run + '-summary.json')).write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
