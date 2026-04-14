const STORAGE_KEY = "gridlab-football-board-v1";
const SVG_NS = "http://www.w3.org/2000/svg";
const MAX_HISTORY = 60;
const REGULATION_FIELD_WIDTH_YARDS = 160 / 3;
const FULL_FIELD_LENGTH_YARDS = 120;
const HALF_FIELD_VISIBLE_YARDS = 60;
const FIELD_ART_BLEED = 1.4;

function fitFieldRect(viewWidth, viewHeight, aspect, paddingX, paddingY) {
  const availableWidth = viewWidth - paddingX * 2;
  const availableHeight = viewHeight - paddingY * 2;
  const width = Math.min(availableWidth, availableHeight * aspect);
  const height = width / aspect;
  return {
    x: Number(((viewWidth - width) / 2).toFixed(2)),
    y: Number(((viewHeight - height) / 2).toFixed(2)),
    width: Number(width.toFixed(2)),
    height: Number(height.toFixed(2)),
  };
}

const FIELD_PRESETS = {
  half: {
    key: "half",
    label: "상단 엔드존 하프필드",
    orientation: "vertical",
    visibleYards: 120,
    endzoneYards: 10,
    viewBox: { width: 1280, height: 1400 },
    fieldRect: fitFieldRect(
      1280,
      1400,
      REGULATION_FIELD_WIDTH_YARDS / FULL_FIELD_LENGTH_YARDS,
      132,
      88,
    ),
  },
  full: {
    key: "full",
    label: "좌우 엔드존 풀필드",
    orientation: "horizontal",
    visibleYards: 120,
    endzoneYards: 10,
    viewBox: { width: 1840, height: 1040 },
    fieldRect: fitFieldRect(
      1840,
      1040,
      FULL_FIELD_LENGTH_YARDS / REGULATION_FIELD_WIDTH_YARDS,
      144,
      132,
    ),
  },
};

const TOOL_LABELS = {
  select: "선택",
  offense: "공격 추가",
  defense: "수비 추가",
  neutral: "중립 추가",
  ball: "공 배치",
  path: "라우트 그리기",
  motion: "모션 경로",
  block: "블로킹 경로",
  rush: "패스러시 경로",
  zone: "영역 그리기",
  coverage: "커버리지 원형",
  text: "텍스트 배치",
};

const ROUTE_PRESET_DEFS = [
  { key: "flat", label: "1 Flat" },
  { key: "slant", label: "2 Slant" },
  { key: "comeback", label: "3 Comeback" },
  { key: "curl", label: "4 Curl" },
  { key: "out", label: "5 Out" },
  { key: "drag", label: "6 Drag" },
  { key: "corner", label: "7 Corner" },
  { key: "post", label: "8 Post" },
  { key: "fly", label: "9 Fly" },
];

const CONCEPT_PRESET_DEFS = [
  { key: "inside-switch", label: "Inside Switch", playbook: "Run Heavy", formation: "Gun Bunch TE" },
  { key: "stick", label: "Stick", playbook: "West Coast", formation: "Shotgun Bunch" },
  { key: "mesh-post", label: "Mesh Post", playbook: "Colts", formation: "Shotgun Bunch Offset" },
  { key: "x-spot", label: "X Spot", playbook: "Lions", formation: "Gun Trips TE" },
  { key: "slot-post", label: "Slot Post", playbook: "Jets", formation: "Shotgun Tight" },
  { key: "post-cross", label: "Post Cross", playbook: "Texans", formation: "Shotgun Bunch" },
  { key: "drive-out", label: "Drive Out", playbook: "Saints", formation: "Gun Tight Offset" },
  { key: "bucs-post", label: "Bucs Post", playbook: "Buccaneers", formation: "Shotgun Tight" },
  { key: "clearout-fl-in", label: "Clearout FL In", playbook: "Commanders", formation: "Gun Bunch" },
  { key: "pa-read", label: "PA Read", playbook: "Eagles/Cardinals", formation: "Gun Bunch / Gun Cluster" },
  { key: "verticals", label: "Verticals", playbook: "Cowboys/Giants", formation: "Gun Trips TE" },
  { key: "y-option-wheel", label: "Y-Option Wheel", playbook: "Patriots", formation: "Gun U Trips Wk" },
  { key: "pa-boot-over", label: "PA Boot Over", playbook: "Chiefs", formation: "Shotgun Bunch TE" },
  { key: "y-curl", label: "Y Curl", playbook: "Titans", formation: "Shotgun Bunch" },
  { key: "cross", label: "Cross", playbook: "Jaguars/Vikings", formation: "Shotgun Bunch / Tight Flex" },
  { key: "verts-hb-under", label: "Verts HB Under", playbook: "Bengals", formation: "Shotgun Bunch Offset" },
  { key: "shake-hb-corner", label: "Shake HB Corner", playbook: "Broncos", formation: "Doubles HB Wk" },
  { key: "y-out", label: "Y Out", playbook: "Packers", formation: "Gun Tight Offset TE" },
  { key: "curl-flats", label: "Curl Flats", playbook: "Raiders", formation: "Shotgun U Trips Wk" },
  { key: "spot", label: "Spot", playbook: "Chargers", formation: "Gun Tight Offset" },
];

const TEAM_COLORS = {
  offense: "#ff5a4f",
  defense: "#2e79ff",
  neutral: "#f4d35e",
};

const LAYER_DEFS = [
  { key: "offense", label: "공격" },
  { key: "defense", label: "수비" },
  { key: "neutral", label: "중립" },
  { key: "ball", label: "공" },
  { key: "path", label: "경로" },
  { key: "zone", label: "영역" },
  { key: "text", label: "텍스트" },
  { key: "markers", label: "기준선" },
];

const HASH_CROSS = {
  left: 38,
  middle: 50,
  right: 62,
};


const FIELD_ART = {
  file: "AmFBfield.svg",
  fullWidth: 403.93701,
  fullHeight: 194.8819,
  innerX: 10.628162,
  innerY: 10.62993,
  innerWidth: 382.68039,
  innerHeight: 173.62204,
  href: "./AmFBfield.svg",
};

const BALL_ART = {
  file: "ball.svg.png",
  width: 18,
  height: 18,
  href: "./ball.svg.png",
};

function defaultLayers() {
  return Object.fromEntries(
    LAYER_DEFS.map((definition) => [definition.key, { visible: true, locked: false }]),
  );
}

function defaultViewOptions() {
  return {
    onionSkin: true,
    snap: true,
  };
}

function defaultPlayMeta() {
  return {
    title: "GridLab Play",
    formation: "Gun Bunch",
    personnel: "11 Personnel",
    down: 1,
    distance: 10,
    ballOn: 22,
    hash: "middle",
    notes: "",
    tags: "concept, install",
  };
}

const state = {
  view: "half",
  tool: "select",
  zoom: 1,
  panX: 0,
  panY: 0,
  routeColor: TEAM_COLORS.offense,
  routeLineStyle: "solid",
  frameDuration: 1400,
  currentFrameIndex: 0,
  frames: [],
  selectedId: null,
  playMeta: defaultPlayMeta(),
  layers: defaultLayers(),
  viewOptions: defaultViewOptions(),
};

const ui = {
  drag: null,
  panDrag: null,
  zoneDraft: null,
  pendingPath: [],
  pointerField: null,
  history: [],
  historyIndex: -1,
  playing: false,
  preview: null,
  rafId: 0,
  playbackStartedAt: 0,
  playbackBaseOffset: 0,
  playbackStartFrame: 0,
  lastSavedAt: null,
  snapGuides: [],
};

const refs = {
  board: document.getElementById("board"),
  boardHint: document.getElementById("boardHint"),
  conceptPresetGrid: document.getElementById("conceptPresetGrid"),
  frameStrip: document.getElementById("frameStrip"),
  inspectorContent: document.getElementById("inspectorContent"),
  playSettingsPanel: document.getElementById("playSettingsPanel"),
  layerPanel: document.getElementById("layerPanel"),
  projectSummary: document.getElementById("projectSummary"),
  modeLabel: document.getElementById("modeLabel"),
  routeStyleControls: document.getElementById("routeStyleControls"),
  routeColorInput: document.getElementById("routeColorInput"),
  routeLineStyleSelect: document.getElementById("routeLineStyleSelect"),
  zoomRange: document.getElementById("zoomRange"),
  zoomOutBtn: document.getElementById("zoomOutBtn"),
  zoomInBtn: document.getElementById("zoomInBtn"),
  zoomResetBtn: document.getElementById("zoomResetBtn"),
  panUpBtn: document.getElementById("panUpBtn"),
  panLeftBtn: document.getElementById("panLeftBtn"),
  panRightBtn: document.getElementById("panRightBtn"),
  panDownBtn: document.getElementById("panDownBtn"),
  panCenterBtn: document.getElementById("panCenterBtn"),
  zoomValue: document.getElementById("zoomValue"),
  saveStateLabel: document.getElementById("saveStateLabel"),
  frameDurationRange: document.getElementById("frameDurationRange"),
  frameDurationValue: document.getElementById("frameDurationValue"),
  importInput: document.getElementById("importInput"),
  playBtn: document.getElementById("playBtn"),
  snapToggleBtn: document.getElementById("snapToggleBtn"),
  onionSkinBtn: document.getElementById("onionSkinBtn"),
  finishPathBtn: document.getElementById("finishPathBtn"),
  cancelPathBtn: document.getElementById("cancelPathBtn"),
  tweenFrameBtn: document.getElementById("tweenFrameBtn"),
};

function uid() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function clone(value) {
  return structuredClone(value);
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function round(value, precision = 2) {
  return Number(value.toFixed(precision));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function slugifyFilename(value) {
  return String(value || "gridlab-play")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u3131-\uD79D]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60) || "gridlab-play";
}

function objectLayerKey(object) {
  if (object.kind === "player") {
    return object.team;
  }
  return object.kind;
}

function isLayerVisible(layerKey) {
  return state.layers[layerKey]?.visible !== false;
}

function isLayerLocked(layerKey) {
  return state.layers[layerKey]?.locked === true;
}

function isObjectVisible(object) {
  return isLayerVisible(objectLayerKey(object));
}

function isObjectLocked(object) {
  return isLayerLocked(objectLayerKey(object));
}

function lengthFromBallOn(ballOn) {
  const yardLine = clamp(Number(ballOn) || 22, 1, 99);
  return clamp(round(100 - ((yardLine + 10) / 120) * 100), 0, 100);
}

function ballOnFromLength(length) {
  const raw = ((100 - clamp(Number(length) || 0, 0, 100)) / 100) * 120 - 10;
  return clamp(round(raw), 1, 99);
}

function hashKeyFromCross(cross) {
  if (cross <= 44) {
    return "left";
  }
  if (cross >= 56) {
    return "right";
  }
  return "middle";
}

function ballOnLabel(ballOn) {
  const yardLine = clamp(Number(ballOn) || 22, 1, 99);
  if (yardLine === 50) {
    return "50";
  }
  if (yardLine < 50) {
    return `Own ${yardLine}`;
  }
  return `Opp ${100 - yardLine}`;
}

function inferPlayMetaFromFrames(frames = []) {
  const fallback = defaultPlayMeta();
  const firstFrame = frames[0];
  const ball = firstFrame?.objects?.find((object) => object.kind === "ball");
  return {
    ...fallback,
    title: firstFrame?.name || fallback.title,
    ballOn: ball ? ballOnFromLength(ball.length) : fallback.ballOn,
    hash: ball ? hashKeyFromCross(ball.cross) : fallback.hash,
  };
}

function normalizeLayers(layers) {
  const base = defaultLayers();
  if (!layers || typeof layers !== "object") {
    return base;
  }
  for (const definition of LAYER_DEFS) {
    const next = layers[definition.key] || {};
    base[definition.key] = {
      visible: next.visible !== false,
      locked: next.locked === true,
    };
  }
  return base;
}

function normalizeViewOptions(options) {
  return {
    onionSkin: options?.onionSkin !== false,
    snap: options?.snap !== false,
  };
}

function normalizePlayMeta(meta, frames) {
  const inferred = inferPlayMetaFromFrames(frames);
  return {
    ...defaultPlayMeta(),
    ...inferred,
    ...(meta || {}),
    down: clamp(Number(meta?.down || inferred.down || 1), 1, 4),
    distance: clamp(Number(meta?.distance || inferred.distance || 10), 1, 40),
    ballOn: clamp(Number(meta?.ballOn || inferred.ballOn || 22), 1, 99),
    hash: ["left", "middle", "right"].includes(meta?.hash) ? meta.hash : inferred.hash,
  };
}

function teamColor(team) {
  return TEAM_COLORS[team] || "#ffffff";
}

function createPlayer(team, cross, length, overrides = {}) {
  const existing = getCurrentFrame()?.objects.filter(
    (object) => object.kind === "player" && object.team === team,
  ).length ?? 0;
  return {
    id: uid(),
    kind: "player",
    team,
    cross,
    length,
    label:
      overrides.label ||
      (team === "offense"
        ? ["QB", "RB", "WR", "TE", "OL"][existing % 5]
        : team === "defense"
          ? ["CB", "S", "LB", "DL"][existing % 4]
          : "N"),
    number: overrides.number || "",
    roleId: overrides.roleId || "",
    aliases: Array.isArray(overrides.aliases) ? overrides.aliases : [],
    size: overrides.size || "large",
    rotation: overrides.rotation || 0,
    color: overrides.color || teamColor(team),
  };
}

function createBall(cross, length, overrides = {}) {
  return {
    id: uid(),
    kind: "ball",
    cross,
    length,
    rotation: overrides.rotation ?? -18,
    scale: overrides.scale ?? 1,
  };
}

function createPath(points, overrides = {}) {
  const lineStyle = ["solid", "dashed", "motion"].includes(overrides.lineStyle)
    ? overrides.lineStyle
    : overrides.dashed
      ? "dashed"
      : "solid";
  return {
    id: uid(),
    kind: "path",
    points,
    color: overrides.color || TEAM_COLORS.offense,
    width: overrides.width ?? 3.8,
    dashed: overrides.dashed ?? lineStyle !== "solid",
    lineStyle,
    arrow: overrides.arrow ?? true,
    label: overrides.label || "",
    opacity: overrides.opacity ?? 1,
    roleId: overrides.roleId || "",
    systemMarker: overrides.systemMarker === true,
  };
}

function isLineDrawingTool(tool = state.tool) {
  return tool === "path" || tool === "motion" || tool === "block" || tool === "rush";
}

function resolvePathLineStyle(object) {
  if (["solid", "dashed", "motion"].includes(object?.lineStyle)) {
    return object.lineStyle;
  }
  return object?.dashed ? "dashed" : "solid";
}

function strokeDashArrayForPath(object) {
  const lineStyle = resolvePathLineStyle(object);
  if (lineStyle === "motion") {
    return "8 12";
  }
  if (lineStyle === "dashed") {
    return "10 12";
  }
  return "";
}

function strokeLinecapForPath(object) {
  if (resolvePathLineStyle(object) === "motion") {
    return "round";
  }
  return object.arrow ? "butt" : "round";
}

function pathStyleForTool(tool, selected) {
  if (tool === "block") {
    return {
      color: TEAM_COLORS.offense,
      width: 5.4,
      arrow: false,
      dashed: false,
      lineStyle: "solid",
      opacity: 0.96,
      label: "",
    };
  }

  if (tool === "rush") {
    return {
      color: TEAM_COLORS.defense,
      width: 4.8,
      arrow: true,
      dashed: false,
      lineStyle: "solid",
      opacity: 0.98,
      label: "",
    };
  }

  if (tool === "motion") {
    return {
      color: state.routeColor,
      width: 3.8,
      arrow: true,
      dashed: true,
      lineStyle: "motion",
      opacity: 0.98,
      label: "",
    };
  }

  return {
    color: state.routeColor || (
      selected?.kind === "player"
        ? selected.color
        : selected?.kind === "path"
          ? selected.color
          : TEAM_COLORS.offense
    ),
    width: 4,
    arrow: state.routeLineStyle !== "solid" ? true : true,
    dashed: state.routeLineStyle !== "solid",
    lineStyle: state.routeLineStyle,
    opacity: 1,
    label: "",
  };
}

function offsetRoutePoint(origin, crossOffset, lengthOffset) {
  return {
    cross: clamp(round(origin.cross + crossOffset), 0, 100),
    length: clamp(round(origin.length + lengthOffset), 0, 100),
  };
}

function routePresetPoints(key, origin) {
  const outsideDir = origin.cross >= 50 ? 1 : -1;
  const insideDir = -outsideDir;

  if (key === "flat") {
    return [
      offsetRoutePoint(origin, 0, 0),
      offsetRoutePoint(origin, 0, -8),
      offsetRoutePoint(origin, outsideDir * 18, -8),
    ];
  }

  if (key === "slant") {
    return [
      offsetRoutePoint(origin, 0, 0),
      offsetRoutePoint(origin, 0, -8),
      offsetRoutePoint(origin, insideDir * 17, -24),
    ];
  }

  if (key === "comeback") {
    return [
      offsetRoutePoint(origin, 0, 0),
      offsetRoutePoint(origin, 0, -27),
      offsetRoutePoint(origin, outsideDir * 13, -18),
    ];
  }

  if (key === "curl") {
    return [
      offsetRoutePoint(origin, 0, 0),
      offsetRoutePoint(origin, 0, -24),
      offsetRoutePoint(origin, insideDir * 6, -18),
      offsetRoutePoint(origin, 0, -16),
    ];
  }

  if (key === "out") {
    return [
      offsetRoutePoint(origin, 0, 0),
      offsetRoutePoint(origin, 0, -17),
      offsetRoutePoint(origin, outsideDir * 20, -17),
    ];
  }

  if (key === "drag") {
    return [
      offsetRoutePoint(origin, 0, 0),
      offsetRoutePoint(origin, 0, -9),
      offsetRoutePoint(origin, insideDir * 25, -9),
    ];
  }

  if (key === "corner") {
    return [
      offsetRoutePoint(origin, 0, 0),
      offsetRoutePoint(origin, 0, -27),
      offsetRoutePoint(origin, outsideDir * 18, -41),
    ];
  }

  if (key === "post") {
    return [
      offsetRoutePoint(origin, 0, 0),
      offsetRoutePoint(origin, 0, -27),
      offsetRoutePoint(origin, insideDir * 16, -41),
    ];
  }

  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -42),
  ];
}

function insertRoutePreset(key) {
  const preset = ROUTE_PRESET_DEFS.find((item) => item.key === key);
  if (!preset || isLayerLocked("path")) {
    return;
  }

  const selected = findObject(state.selectedId);
  const origin =
    selected?.kind === "player"
      ? { cross: selected.cross, length: selected.length }
      : { cross: 50, length: 82 };
  const color =
    selected?.kind === "player" ? selected.color || teamColor(selected.team) : TEAM_COLORS.offense;

  const route = createPath(routePresetPoints(key, origin), {
    color,
    label: preset.label,
    width: 4,
  });

  addObjectToCurrentFrame(route);
  commitProject();
}

function createZone(cross, length, crossSize, lengthSize, overrides = {}) {
  return {
    id: uid(),
    kind: "zone",
    cross,
    length,
    crossSize,
    lengthSize,
    shape: overrides.shape || "rect",
    color: overrides.color || "#ffd166",
    opacity: overrides.opacity ?? 0.22,
    label: overrides.label || "",
  };
}

function zoneStyleForTool(tool = state.tool) {
  if (tool === "coverage") {
    return {
      shape: "ellipse",
      color: TEAM_COLORS.defense,
      opacity: 0.2,
      label: "",
    };
  }

  return {
    shape: "rect",
    color: "#ffd166",
    opacity: 0.22,
    label: "",
  };
}

function createText(cross, length, text, overrides = {}) {
  return {
    id: uid(),
    kind: "text",
    cross,
    length,
    text,
    color: overrides.color || "#f6f6f6",
    fontSize: overrides.fontSize ?? 28,
    align: overrides.align || "middle",
  };
}

function offenseSkillPlayer(cross, length, label, roleId, overrides = {}) {
  return createPlayer("offense", cross, length, {
    label,
    roleId,
    number: overrides.number ?? roleId,
    ...overrides,
  });
}

function defenseShellPlayers() {
  return [
    createPlayer("defense", 12, 66, { label: "CB" }),
    createPlayer("defense", 28, 74, { label: "DE" }),
    createPlayer("defense", 40, 74, { label: "DT" }),
    createPlayer("defense", 50, 74, { label: "NT" }),
    createPlayer("defense", 60, 74, { label: "DT" }),
    createPlayer("defense", 72, 74, { label: "DE" }),
    createPlayer("defense", 30, 67, { label: "OLB" }),
    createPlayer("defense", 50, 65, { label: "MLB" }),
    createPlayer("defense", 70, 67, { label: "OLB" }),
    createPlayer("defense", 40, 58, { label: "FS" }),
    createPlayer("defense", 88, 66, { label: "CB" }),
  ];
}

function defaultElevenPersonnelOffense() {
  return [
    createPlayer("offense", 12, 76, { label: "WR", roleId: "X" }),
    createPlayer("offense", 27, 72, { label: "WR", roleId: "H" }),
    createPlayer("offense", 32, 78, { label: "LT", roleId: "LT", number: "" }),
    createPlayer("offense", 41, 78, { label: "LG", roleId: "LG", number: "" }),
    createPlayer("offense", 50, 78, { label: "C", roleId: "C", number: "" }),
    createPlayer("offense", 59, 78, { label: "RG", roleId: "RG", number: "" }),
    createPlayer("offense", 68, 78, { label: "RT", roleId: "RT", number: "" }),
    createPlayer("offense", 77, 79, { label: "TE", roleId: "Y" }),
    createPlayer("offense", 88, 76, { label: "WR", roleId: "Z" }),
    createPlayer("offense", 50, 83, { label: "QB", roleId: "QB", number: "12" }),
    createPlayer("offense", 50, 89, { label: "RB", roleId: "HB", number: "22" }),
  ];
}

function defaultFourThreeDefense() {
  return [
    createPlayer("defense", 14, 62, { label: "CB", roleId: "LCB" }),
    createPlayer("defense", 34, 67, { label: "OLB", roleId: "WLB" }),
    createPlayer("defense", 32, 73, { label: "DE", roleId: "LDE" }),
    createPlayer("defense", 44, 73, { label: "DT", roleId: "LDT" }),
    createPlayer("defense", 50, 65, { label: "MLB", roleId: "MLB" }),
    createPlayer("defense", 56, 73, { label: "DT", roleId: "RDT" }),
    createPlayer("defense", 68, 73, { label: "DE", roleId: "RDE" }),
    createPlayer("defense", 66, 67, { label: "OLB", roleId: "SLB" }),
    createPlayer("defense", 86, 62, { label: "CB", roleId: "RCB" }),
    createPlayer("defense", 40, 56, { label: "FS", roleId: "FS" }),
    createPlayer("defense", 60, 58, { label: "SS", roleId: "SS" }),
  ];
}

function inferBallSpot(objects) {
  const center = objects.find(
    (object) => object.kind === "player" && object.team === "offense" && object.label === "C",
  );
  if (center) {
    return {
      cross: center.cross,
      length: clamp(center.length - 0.8, 0, 100),
      rotation: -12,
    };
  }

  const qb = objects.find(
    (object) => object.kind === "player" && object.team === "offense" && object.label === "QB",
  );
  if (qb) {
    return {
      cross: qb.cross,
      length: clamp(qb.length - 5.5, 0, 100),
      rotation: -18,
    };
  }

  return { cross: 50, length: 78, rotation: -18 };
}

function ensureSingleBall(frame) {
  if (!frame || !Array.isArray(frame.objects)) {
    return frame;
  }

  const sanitized = frame.objects.filter((object) => !isLegacyMarker(object));
  const withoutBalls = sanitized.filter((object) => object.kind !== "ball");
  const existingBall = frame.objects.find((object) => object.kind === "ball");
  const spot = existingBall
    ? {
        cross: existingBall.cross,
        length: existingBall.length,
        rotation: existingBall.rotation ?? -18,
        scale: existingBall.scale ?? 1,
      }
    : inferBallSpot(withoutBalls);

  return {
    ...frame,
    objects: [...withoutBalls, createBall(spot.cross, spot.length, spot)],
  };
}

function normalizeFrames(frames) {
  return Array.isArray(frames) ? frames.map((frame) => ensureSingleBall(frame)) : [];
}

function isLegacyMarker(object) {
  return (
    object?.kind === "path" &&
    (object.systemMarker === true || (
      ["LOS", "1ST"].includes(object.label) &&
      object.arrow === false &&
      Number(object.width).toFixed(1) === "3.2" &&
      resolvePathLineStyle(object) === "dashed"
    ))
  );
}

function driveMarkers(meta = state.playMeta) {
  const losLength = lengthFromBallOn(meta.ballOn);
  const gainLineBallOn = clamp(meta.ballOn + meta.distance, 1, 99);
  const gainLineLength = lengthFromBallOn(gainLineBallOn);
  return [
    createPath(
      [
        { cross: 3, length: losLength },
        { cross: 97, length: losLength },
      ],
      {
        color: "#f7d85c",
        width: 3.2,
        dashed: true,
        arrow: false,
        label: "LOS",
        systemMarker: true,
      },
    ),
    createPath(
      [
        { cross: 3, length: gainLineLength },
        { cross: 97, length: gainLineLength },
      ],
      {
        color: "#84f6a0",
        width: 3.2,
        dashed: true,
        arrow: false,
        label: "1ST",
        systemMarker: true,
      },
    ),
  ];
}

function offensiveLinePlayers(linePositions = [28, 38, 50, 62, 72], length = 80) {
  const labels = ["LT", "LG", "C", "RG", "RT"];
  const roles = ["LT", "LG", "C", "RG", "RT"];
  return linePositions.map((cross, index) =>
    offenseSkillPlayer(cross, length, labels[index], roles[index], {
      number: "",
    }),
  );
}

function buildOffensiveFormationPlayers(formation) {
  const line = offensiveLinePlayers();

  if (formation === "trips-te") {
    return [
      ...line,
      offenseSkillPlayer(14, 76, "WR", "X"),
      offenseSkillPlayer(68, 75, "WR", "H"),
      offenseSkillPlayer(80, 80, "TE", "Y"),
      offenseSkillPlayer(91, 76, "WR", "Z"),
      offenseSkillPlayer(50, 85, "QB", "QB"),
      offenseSkillPlayer(50, 91, "HB", "HB"),
    ];
  }

  if (formation === "tight") {
    return [
      ...line,
      offenseSkillPlayer(16, 76, "WR", "X"),
      offenseSkillPlayer(64, 76, "WR", "S1"),
      offenseSkillPlayer(72, 76, "WR", "S2"),
      offenseSkillPlayer(80, 80, "TE", "Y"),
      offenseSkillPlayer(50, 85, "QB", "QB"),
      offenseSkillPlayer(50, 91, "HB", "HB"),
    ];
  }

  if (formation === "tight-offset") {
    return [
      ...line,
      offenseSkillPlayer(16, 76, "WR", "X"),
      offenseSkillPlayer(64, 76, "WR", "S1", { aliases: ["Z"] }),
      offenseSkillPlayer(72, 76, "WR", "S2"),
      offenseSkillPlayer(80, 80, "TE", "Y"),
      offenseSkillPlayer(50, 85, "QB", "QB"),
      offenseSkillPlayer(40, 89, "HB", "HB"),
    ];
  }

  if (formation === "u-trips-wk") {
    return [
      ...line,
      offenseSkillPlayer(14, 76, "WR", "X"),
      offenseSkillPlayer(58, 76, "WR", "F"),
      offenseSkillPlayer(68, 75, "WR", "H"),
      offenseSkillPlayer(79, 80, "TE", "Y"),
      offenseSkillPlayer(91, 76, "WR", "Z"),
      offenseSkillPlayer(50, 85, "QB", "QB"),
    ];
  }

  if (formation === "doubles-hb-wk") {
    return [
      ...line,
      offenseSkillPlayer(18, 76, "WR", "X"),
      offenseSkillPlayer(36, 76, "WR", "H"),
      offenseSkillPlayer(80, 80, "TE", "Y"),
      offenseSkillPlayer(90, 76, "WR", "Z"),
      offenseSkillPlayer(50, 85, "QB", "QB"),
      offenseSkillPlayer(40, 89, "HB", "HB"),
    ];
  }

  if (formation === "bunch-te") {
    return [
      ...line,
      offenseSkillPlayer(18, 76, "WR", "X"),
      offenseSkillPlayer(73, 80, "TE", "B1", { aliases: ["Y"] }),
      offenseSkillPlayer(85, 74, "WR", "B2"),
      offenseSkillPlayer(85, 80, "WR", "B3"),
      offenseSkillPlayer(50, 85, "QB", "QB"),
      offenseSkillPlayer(50, 91, "HB", "HB"),
    ];
  }

  if (formation === "bunch-offset") {
    return [
      ...line,
      offenseSkillPlayer(18, 76, "WR", "X"),
      offenseSkillPlayer(79, 77, "WR", "B1"),
      offenseSkillPlayer(85, 74, "WR", "B2"),
      offenseSkillPlayer(85, 80, "WR", "B3"),
      offenseSkillPlayer(50, 85, "QB", "QB"),
      offenseSkillPlayer(40, 89, "HB", "HB"),
    ];
  }

  return [
    ...line,
    offenseSkillPlayer(18, 76, "WR", "X"),
    offenseSkillPlayer(79, 77, "WR", "B1"),
    offenseSkillPlayer(85, 74, "WR", "B2"),
    offenseSkillPlayer(85, 80, "WR", "B3"),
    offenseSkillPlayer(50, 85, "QB", "QB"),
    offenseSkillPlayer(50, 91, "HB", "HB"),
  ];
}

function playerMap(players) {
  const map = new Map();
  players.forEach((player) => {
    const keys = [player.roleId, player.label, ...(player.aliases || [])].filter(Boolean);
    keys.forEach((key) => {
      if (!map.has(key)) {
        map.set(key, player);
      }
    });
  });
  return map;
}

function outsideDirection(player) {
  return player.cross >= 50 ? 1 : -1;
}

function insideDirection(player) {
  return outsideDirection(player) * -1;
}

function routeVertical(origin, depth = 40) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -depth),
  ];
}

function routePost(origin, dir, stem = 24, breakCross = 16, breakDepth = 16) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -stem),
    offsetRoutePoint(origin, dir * breakCross, -(stem + breakDepth)),
  ];
}

function routeCorner(origin, dir, stem = 24, breakCross = 18, breakDepth = 14) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -stem),
    offsetRoutePoint(origin, dir * breakCross, -(stem + breakDepth)),
  ];
}

function routeFlatPath(origin, dir, stem = 7, width = 18) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -stem),
    offsetRoutePoint(origin, dir * width, -stem),
  ];
}

function routeOutPath(origin, dir, depth = 16, width = 18) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -depth),
    offsetRoutePoint(origin, dir * width, -depth),
  ];
}

function routeCurlPath(origin, dir, depth = 18) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -depth),
    offsetRoutePoint(origin, dir * 4, -(depth - 4)),
    offsetRoutePoint(origin, 0, -(depth - 2)),
  ];
}

function routeComebackPath(origin, dir, depth = 28, width = 12, settleDepth = 19) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -depth),
    offsetRoutePoint(origin, dir * width, -settleDepth),
  ];
}

function routeDragPath(origin, dir, depth = 9, width = 28) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -depth),
    offsetRoutePoint(origin, dir * width, -depth),
  ];
}

function routeDigPath(origin, dir, depth = 24, width = 20) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -depth),
    offsetRoutePoint(origin, dir * width, -depth),
  ];
}

function routeWheelPath(origin, dir) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, dir * 8, -7),
    offsetRoutePoint(origin, dir * 14, -18),
    offsetRoutePoint(origin, dir * 18, -34),
  ];
}

function routeAnglePath(origin, dir) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -7),
    offsetRoutePoint(origin, dir * 9, -15),
    offsetRoutePoint(origin, dir * 16, -23),
  ];
}

function routeStickPath(origin, dir) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -9),
    offsetRoutePoint(origin, dir * 5, -8),
  ];
}

function routeCrossPath(origin, dir, stem = 12, width = 34, extraDepth = 10) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -stem),
    offsetRoutePoint(origin, dir * width, -(stem + extraDepth)),
  ];
}

function routeOptionPath(origin, dir) {
  return [
    offsetRoutePoint(origin, 0, 0),
    offsetRoutePoint(origin, 0, -9),
    offsetRoutePoint(origin, dir * 8, -13),
    offsetRoutePoint(origin, dir * 15, -18),
  ];
}

function routePathForRole(map, roleId, builder) {
  const player = map.get(roleId);
  if (!player) {
    return null;
  }
  const path = createPath(builder(player), {
    color: TEAM_COLORS.offense,
    width: 4,
  });
  path.roleId = roleId;
  return path;
}

function conceptRoutesForPreset(presetKey, map) {
  const concepts = {
    "inside-switch": [
      routePathForRole(map, "B2", (player) => routePost(player, insideDirection(player), 22, 18, 16)),
      routePathForRole(map, "B1", (player) => routeCorner(player, outsideDirection(player), 20, 15, 14)),
      routePathForRole(map, "B3", (player) => routeFlatPath(player, outsideDirection(player), 6, 16)),
      routePathForRole(map, "X", (player) => routeDigPath(player, insideDirection(player), 20, 18)),
      routePathForRole(map, "HB", (player) => routeAnglePath(player, outsideDirection(player))),
    ],
    stick: [
      routePathForRole(map, "B1", (player) => routeStickPath(player, insideDirection(player))),
      routePathForRole(map, "B2", (player) => routeCorner(player, outsideDirection(player), 20, 15, 14)),
      routePathForRole(map, "B3", (player) => routeFlatPath(player, outsideDirection(player), 6, 18)),
      routePathForRole(map, "X", (player) => routeDigPath(player, insideDirection(player), 20, 16)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, insideDirection(player), 5, 10)),
    ],
    "mesh-post": [
      routePathForRole(map, "B2", (player) => routePost(player, insideDirection(player), 22, 17, 17)),
      routePathForRole(map, "B1", (player) => routeDragPath(player, insideDirection(player), 8, 34)),
      routePathForRole(map, "B3", (player) => routeDragPath(player, insideDirection(player), 11, 27)),
      routePathForRole(map, "X", (player) => routeDigPath(player, insideDirection(player), 22, 16)),
      routePathForRole(map, "HB", (player) => routeWheelPath(player, outsideDirection(player))),
    ],
    "x-spot": [
      routePathForRole(map, "X", (player) => routeOutPath(player, outsideDirection(player), 8, 14)),
      routePathForRole(map, "H", (player) => routeCorner(player, outsideDirection(player), 20, 14, 12)),
      routePathForRole(map, "Y", (player) => routeFlatPath(player, outsideDirection(player), 6, 14)),
      routePathForRole(map, "Z", (player) => routeDigPath(player, insideDirection(player), 22, 16)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, insideDirection(player), 5, 12)),
    ],
    "slot-post": [
      routePathForRole(map, "S2", (player) => routePost(player, insideDirection(player), 22, 18, 16)),
      routePathForRole(map, "S1", (player) => routeDragPath(player, insideDirection(player), 9, 24)),
      routePathForRole(map, "Y", (player) => routeOutPath(player, outsideDirection(player), 12, 16)),
      routePathForRole(map, "X", (player) => routeDigPath(player, insideDirection(player), 22, 18)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, outsideDirection(player), 6, 14)),
    ],
    "post-cross": [
      routePathForRole(map, "B2", (player) => routePost(player, insideDirection(player), 22, 16, 16)),
      routePathForRole(map, "B1", (player) => routeCrossPath(player, insideDirection(player), 10, 34, 14)),
      routePathForRole(map, "B3", (player) => routeFlatPath(player, outsideDirection(player), 5, 14)),
      routePathForRole(map, "X", (player) => routeDigPath(player, insideDirection(player), 20, 17)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, insideDirection(player), 5, 12)),
    ],
    "drive-out": [
      routePathForRole(map, "S1", (player) => routeCrossPath(player, insideDirection(player), 10, 28, 8)),
      routePathForRole(map, "S2", (player) => routeDigPath(player, insideDirection(player), 20, 17)),
      routePathForRole(map, "Y", (player) => routeOutPath(player, outsideDirection(player), 14, 16)),
      routePathForRole(map, "X", (player) => routeCurlPath(player, outsideDirection(player), 16)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, insideDirection(player), 5, 14)),
    ],
    "bucs-post": [
      routePathForRole(map, "S2", (player) => routePost(player, insideDirection(player), 22, 18, 17)),
      routePathForRole(map, "S1", (player) => routeVertical(player, 34)),
      routePathForRole(map, "Y", (player) => routeOutPath(player, outsideDirection(player), 13, 16)),
      routePathForRole(map, "X", (player) => routeCrossPath(player, insideDirection(player), 12, 30, 12)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, outsideDirection(player), 5, 14)),
    ],
    "clearout-fl-in": [
      routePathForRole(map, "B2", (player) => routeVertical(player, 40)),
      routePathForRole(map, "B1", (player) => routeCrossPath(player, insideDirection(player), 12, 26, 8)),
      routePathForRole(map, "B3", (player) => routeFlatPath(player, outsideDirection(player), 5, 12)),
      routePathForRole(map, "X", (player) => routePost(player, insideDirection(player), 22, 15, 16)),
      routePathForRole(map, "HB", (player) => routeAnglePath(player, outsideDirection(player))),
    ],
    "pa-read": [
      routePathForRole(map, "B2", (player) => routeCorner(player, outsideDirection(player), 22, 16, 14)),
      routePathForRole(map, "B1", (player) => routePost(player, insideDirection(player), 22, 16, 16)),
      routePathForRole(map, "B3", (player) => routeDragPath(player, insideDirection(player), 10, 28)),
      routePathForRole(map, "X", (player) => routeComebackPath(player, outsideDirection(player), 26, 10, 18)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, outsideDirection(player), 6, 15)),
    ],
    verticals: [
      routePathForRole(map, "X", (player) => routeVertical(player, 42)),
      routePathForRole(map, "H", (player) => routeVertical(player, 36)),
      routePathForRole(map, "Y", (player) => routeVertical(player, 34)),
      routePathForRole(map, "Z", (player) => routeVertical(player, 42)),
      routePathForRole(map, "HB", (player) => routeAnglePath(player, outsideDirection(player))),
    ],
    "y-option-wheel": [
      routePathForRole(map, "Y", (player) => routeOptionPath(player, insideDirection(player))),
      routePathForRole(map, "F", (player) => routeWheelPath(player, outsideDirection(player))),
      routePathForRole(map, "H", (player) => routeDigPath(player, insideDirection(player), 18, 16)),
      routePathForRole(map, "Z", (player) => routeVertical(player, 36)),
      routePathForRole(map, "X", (player) => routeCurlPath(player, outsideDirection(player), 16)),
    ],
    "pa-boot-over": [
      routePathForRole(map, "Y", (player) => routeCrossPath(player, insideDirection(player), 10, 36, 18)),
      routePathForRole(map, "B2", (player) => routeCorner(player, outsideDirection(player), 24, 18, 14)),
      routePathForRole(map, "X", (player) => routeComebackPath(player, outsideDirection(player), 26, 10, 18)),
      routePathForRole(map, "B3", (player) => routeFlatPath(player, outsideDirection(player), 5, 12)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, outsideDirection(player), 7, 18)),
    ],
    "y-curl": [
      routePathForRole(map, "B1", (player) => routeCurlPath(player, insideDirection(player), 15)),
      routePathForRole(map, "B2", (player) => routeCorner(player, outsideDirection(player), 22, 16, 14)),
      routePathForRole(map, "B3", (player) => routeFlatPath(player, outsideDirection(player), 5, 12)),
      routePathForRole(map, "X", (player) => routeDigPath(player, insideDirection(player), 22, 18)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, insideDirection(player), 6, 12)),
    ],
    cross: [
      routePathForRole(map, "B1", (player) => routeCrossPath(player, insideDirection(player), 10, 34, 16)),
      routePathForRole(map, "B2", (player) => routePost(player, insideDirection(player), 22, 15, 14)),
      routePathForRole(map, "B3", (player) => routeFlatPath(player, outsideDirection(player), 5, 12)),
      routePathForRole(map, "X", (player) => routeDigPath(player, insideDirection(player), 20, 16)),
      routePathForRole(map, "HB", (player) => routeAnglePath(player, outsideDirection(player))),
    ],
    "verts-hb-under": [
      routePathForRole(map, "B1", (player) => routeVertical(player, 36)),
      routePathForRole(map, "B2", (player) => routeVertical(player, 40)),
      routePathForRole(map, "B3", (player) => routeVertical(player, 34)),
      routePathForRole(map, "X", (player) => routeVertical(player, 38)),
      routePathForRole(map, "HB", (player) => routeDragPath(player, insideDirection(player), 10, 32)),
    ],
    "shake-hb-corner": [
      routePathForRole(map, "X", (player) => routeVertical(player, 34)),
      routePathForRole(map, "H", (player) => routeDigPath(player, insideDirection(player), 16, 16)),
      routePathForRole(map, "Y", (player) => routeCorner(player, outsideDirection(player), 18, 16, 16)),
      routePathForRole(map, "Z", (player) => routePost(player, insideDirection(player), 22, 16, 16)),
      routePathForRole(map, "HB", (player) => routeCorner(player, outsideDirection(player), 10, 18, 14)),
    ],
    "y-out": [
      routePathForRole(map, "Y", (player) => routeOutPath(player, outsideDirection(player), 14, 18)),
      routePathForRole(map, "S2", (player) => routePost(player, insideDirection(player), 20, 15, 15)),
      routePathForRole(map, "Z", (player) => routeVertical(player, 34)),
      routePathForRole(map, "X", (player) => routeDragPath(player, insideDirection(player), 10, 26)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, insideDirection(player), 6, 12)),
    ],
    "curl-flats": [
      routePathForRole(map, "H", (player) => routeCurlPath(player, insideDirection(player), 16)),
      routePathForRole(map, "Y", (player) => routeFlatPath(player, outsideDirection(player), 5, 12)),
      routePathForRole(map, "F", (player) => routeFlatPath(player, insideDirection(player), 5, 12)),
      routePathForRole(map, "Z", (player) => routeVertical(player, 34)),
      routePathForRole(map, "X", (player) => routeSlantPoints(player, insideDirection(player))),
    ],
    spot: [
      routePathForRole(map, "S1", (player) => routeCorner(player, outsideDirection(player), 18, 14, 12)),
      routePathForRole(map, "S2", (player) => routeOutPath(player, outsideDirection(player), 8, 14)),
      routePathForRole(map, "Y", (player) => routeFlatPath(player, outsideDirection(player), 5, 14)),
      routePathForRole(map, "X", (player) => routeDigPath(player, insideDirection(player), 20, 16)),
      routePathForRole(map, "HB", (player) => routeFlatPath(player, insideDirection(player), 5, 12)),
    ],
  };

  return (concepts[presetKey] || []).filter(Boolean);
}

function routeSlantPoints(player, dir) {
  return [
    offsetRoutePoint(player, 0, 0),
    offsetRoutePoint(player, 0, -8),
    offsetRoutePoint(player, dir * 16, -24),
  ];
}

function conceptFormationKey(presetKey) {
  const map = {
    "inside-switch": "bunch-te",
    stick: "bunch",
    "mesh-post": "bunch-offset",
    "x-spot": "trips-te",
    "slot-post": "tight",
    "post-cross": "bunch",
    "drive-out": "tight-offset",
    "bucs-post": "tight",
    "clearout-fl-in": "bunch",
    "pa-read": "bunch",
    verticals: "trips-te",
    "y-option-wheel": "u-trips-wk",
    "pa-boot-over": "bunch-te",
    "y-curl": "bunch",
    cross: "bunch",
    "verts-hb-under": "bunch-offset",
    "shake-hb-corner": "doubles-hb-wk",
    "y-out": "tight-offset",
    "curl-flats": "u-trips-wk",
    spot: "tight-offset",
  };

  return map[presetKey] || "bunch";
}

function playerRoleKeys(player) {
  return [player.roleId, player.label, ...(player.aliases || [])].filter(Boolean);
}

function conceptRouteMap(objects) {
  const map = new Map();
  objects.forEach((object) => {
    if (object.kind === "path" && object.roleId) {
      map.set(object.roleId, object);
    }
  });
  return map;
}

function pointAlongPath(points, progress) {
  if (!Array.isArray(points) || !points.length) {
    return { cross: 50, length: 50 };
  }
  if (points.length === 1) {
    return clone(points[0]);
  }

  const normalizedProgress = clamp(progress, 0, 1);
  const segments = [];
  let totalLength = 0;

  for (let index = 1; index < points.length; index += 1) {
    const start = points[index - 1];
    const end = points[index];
    const length = Math.hypot(end.cross - start.cross, end.length - start.length);
    segments.push({ start, end, length });
    totalLength += length;
  }

  if (totalLength <= 0) {
    return clone(points[0]);
  }

  let remaining = totalLength * normalizedProgress;
  for (const segment of segments) {
    if (remaining <= segment.length) {
      const ratio = segment.length <= 0 ? 0 : remaining / segment.length;
      return {
        cross: round(segment.start.cross + (segment.end.cross - segment.start.cross) * ratio),
        length: round(
          segment.start.length + (segment.end.length - segment.start.length) * ratio,
        ),
      };
    }
    remaining -= segment.length;
  }

  return clone(points[points.length - 1]);
}

function moveConceptOffensePlayer(player, routeMap, progress) {
  const route = playerRoleKeys(player)
    .map((key) => routeMap.get(key))
    .find(Boolean);

  if (route) {
    const point = pointAlongPath(route.points, progress);
    return {
      ...player,
      cross: point.cross,
      length: point.length,
    };
  }

  const role = player.roleId || player.label || "";
  if (["LT", "LG", "C", "RG", "RT"].includes(role)) {
    return {
      ...player,
      length: clamp(round(player.length - progress * 4.2), 0, 100),
    };
  }

  if (role === "QB") {
    return {
      ...player,
      cross: clamp(round(player.cross - progress * 1.1), 0, 100),
      length: clamp(round(player.length - progress * 5.4), 0, 100),
    };
  }

  if (role === "HB") {
    return {
      ...player,
      length: clamp(round(player.length - progress * 3.8), 0, 100),
    };
  }

  return player;
}

function moveConceptDefensePlayer(player, progress) {
  const role = player.roleId || player.label || "";

  if (["DE", "DT", "NT", "LDE", "RDE", "LDT", "RDT"].includes(role)) {
    return {
      ...player,
      length: clamp(round(player.length - progress * 1.4), 0, 100),
    };
  }

  let crossShift = 0;
  if (/(CB|FS|SS|S)$/.test(role)) {
    crossShift = player.cross < 50 ? progress * 1.1 : -progress * 1.1;
  } else if (/(OLB|MLB|LB)$/.test(role)) {
    crossShift = player.cross < 50 ? progress * 0.7 : -progress * 0.7;
  }

  return {
    ...player,
    cross: clamp(round(player.cross + crossShift), 0, 100),
    length: clamp(round(player.length - progress * 3.2), 0, 100),
  };
}

function buildConceptMotionFrame(baseFrame, progress, label) {
  const frame = clone(baseFrame);
  const routeMap = conceptRouteMap(baseFrame.objects);

  frame.id = uid();
  frame.name = label;
  frame.objects = frame.objects.map((object) => {
    if (object.kind !== "player") {
      return object;
    }

    if (object.team === "offense") {
      return moveConceptOffensePlayer(object, routeMap, progress);
    }

    if (object.team === "defense") {
      return moveConceptDefensePlayer(object, progress);
    }

    return object;
  });

  const qb = frame.objects.find(
    (object) => object.kind === "player" && playerRoleKeys(object).includes("QB"),
  );
  if (qb) {
    frame.objects = frame.objects.map((object) =>
      object.kind === "ball"
        ? {
            ...object,
            cross: qb.cross,
            length: clamp(round(qb.length - 2.2), 0, 100),
            rotation: round(-14 + progress * 4),
          }
        : object,
    );
  }

  return ensureSingleBall(frame);
}

function buildConceptFrame(definition) {
  const offense = buildOffensiveFormationPlayers(conceptFormationKey(definition.key));
  const map = playerMap(offense);
  const title = createText(50, 48, `${definition.label} · ${definition.playbook}`, {
    fontSize: 20,
    color: "#17211b",
  });
  const subtitle = createText(50, 51.5, definition.formation, {
    fontSize: 15,
    color: "#42574d",
  });

  return ensureSingleBall({
    id: uid(),
    name: `${definition.label} · ${definition.playbook}`,
    objects: [
      ...offense,
      ...defenseShellPlayers(),
      ...conceptRoutesForPreset(definition.key, map),
      title,
      subtitle,
    ],
  });
}

function buildConceptFrames(definition) {
  const baseFrame = buildConceptFrame(definition);
  const stages = [
    {
      progress: 0,
      name: `${definition.label} · 셋업`,
    },
    {
      progress: 0.34,
      name: `${definition.label} · 릴리즈`,
    },
    {
      progress: 0.7,
      name: `${definition.label} · 브레이크`,
    },
  ];

  return stages.map((stage, index) =>
    index === 0
      ? {
          ...clone(baseFrame),
          id: uid(),
          name: stage.name,
        }
      : buildConceptMotionFrame(baseFrame, stage.progress, stage.name),
  );
}

function renderConceptPresetLibrary() {
  refs.conceptPresetGrid.innerHTML = CONCEPT_PRESET_DEFS.map(
    (definition) => `
      <button
        class="secondary-button concept-preset-button"
        data-concept-preset="${definition.key}"
      >
        <strong>${escapeHtml(definition.label)}</strong>
        <small>${escapeHtml(definition.playbook)} · ${escapeHtml(definition.formation)}</small>
      </button>
    `,
  ).join("");
}

function insertConceptPreset(key) {
  const definition = CONCEPT_PRESET_DEFS.find((item) => item.key === key);
  if (!definition) {
    return;
  }

  const frames = buildConceptFrames(definition);
  stopPlayback(false);
  state.view = "half";
  const insertAt = state.currentFrameIndex + 1;
  state.frames.splice(insertAt, 0, ...frames);
  state.currentFrameIndex = insertAt;
  state.selectedId = null;
  const conceptMeta = inferPlayMetaFromFrames([frames[0]]);
  state.playMeta = {
    ...state.playMeta,
    title: definition.label,
    formation: definition.formation,
    personnel: "11 Personnel",
    ballOn: conceptMeta.ballOn,
    hash: conceptMeta.hash,
    notes: `${definition.playbook} 계열 컨셉 프리셋. 셋업/릴리즈/브레이크 3프레임으로 자동 삽입됩니다.`,
    tags: `${definition.key}, concept, ${definition.playbook.toLowerCase()}`,
  };
  commitProject();
}

function buildDefaultFormationProject() {
  const offense = defaultElevenPersonnelOffense();
  const defense = defaultFourThreeDefense();

  return {
    version: 2,
    view: "half",
    frameDuration: 1400,
    playMeta: {
      ...defaultPlayMeta(),
      title: "11 Personnel · 4-3 Base",
      formation: "11 Personnel Base",
      personnel: "11 Personnel",
      down: 1,
      distance: 10,
      ballOn: 22,
      hash: "middle",
      notes: "기본 정렬 프레임. 플레이 설정보다 LOS/1ST 기준선이 자동 갱신됩니다.",
      tags: "base, install",
    },
    layers: defaultLayers(),
    viewOptions: defaultViewOptions(),
    currentFrameIndex: 0,
    frames: [
      {
        id: uid(),
        name: "11 Personnel · 4-3 Base",
        objects: [...offense, ...defense],
      },
    ].map((frame) => ensureSingleBall(frame)),
  };
}

function buildDemoProject() {
  const offense = [
    createPlayer("offense", 12, 83, { label: "WR" }),
    createPlayer("offense", 31, 79, { label: "LT" }),
    createPlayer("offense", 40, 79, { label: "LG" }),
    createPlayer("offense", 50, 79, { label: "C" }),
    createPlayer("offense", 60, 79, { label: "RG" }),
    createPlayer("offense", 69, 79, { label: "RT" }),
    createPlayer("offense", 78, 80, { label: "TE" }),
    createPlayer("offense", 50, 84, { label: "QB", number: "12" }),
    createPlayer("offense", 57, 88, { label: "RB", number: "22" }),
    createPlayer("offense", 25, 77, { label: "SL" }),
    createPlayer("offense", 88, 74, { label: "WR" }),
  ];

  const defense = [
    createPlayer("defense", 18, 68, { label: "CB" }),
    createPlayer("defense", 32, 72, { label: "LB" }),
    createPlayer("defense", 42, 72, { label: "LB" }),
    createPlayer("defense", 50, 72, { label: "MLB" }),
    createPlayer("defense", 58, 72, { label: "LB" }),
    createPlayer("defense", 68, 72, { label: "LB" }),
    createPlayer("defense", 82, 68, { label: "CB" }),
    createPlayer("defense", 38, 63, { label: "S" }),
    createPlayer("defense", 62, 63, { label: "S" }),
    createPlayer("defense", 28, 74, { label: "DE" }),
    createPlayer("defense", 72, 74, { label: "DE" }),
  ];

  const markings = [
    createPath(
      [
        { cross: 12, length: 83 },
        { cross: 18, length: 70 },
        { cross: 25, length: 56 },
      ],
      { color: TEAM_COLORS.offense, width: 3.6, label: "Go" },
    ),
    createPath(
      [
        { cross: 25, length: 77 },
        { cross: 34, length: 70 },
        { cross: 44, length: 68 },
      ],
      { color: TEAM_COLORS.offense, width: 3.6, label: "Slant" },
    ),
    createPath(
      [
        { cross: 78, length: 80 },
        { cross: 77, length: 73 },
        { cross: 70, length: 63 },
        { cross: 58, length: 55 },
      ],
      { color: TEAM_COLORS.offense, width: 3.6, label: "Over" },
    ),
    createPath(
      [
        { cross: 57, length: 88 },
        { cross: 48, length: 80 },
        { cross: 38, length: 70 },
      ],
      { color: TEAM_COLORS.offense, width: 3.6, label: "Check" },
    ),
    createZone(14, 54, 76, 12, {
      color: "#8dd3ff",
      opacity: 0.14,
      label: "Zone Window",
    }),
    createText(49, 52, "Trips Right / Play Action", {
      fontSize: 20,
      color: "#f7f2d5",
    }),
  ];

  const frame1 = {
    id: uid(),
    name: "셋업",
    objects: [...offense, ...defense, ...markings],
  };

  const frame2 = clone(frame1);
  frame2.id = uid();
  frame2.name = "리드 스텝";
  frame2.objects = frame2.objects.map((object) => {
    if (object.kind !== "player") {
      return object;
    }
    const moved = clone(object);
    if (moved.label === "QB") {
      moved.length = 86;
    }
    if (moved.label === "RB") {
      moved.cross = 53;
      moved.length = 82;
    }
    if (moved.label === "TE") {
      moved.length = 72;
      moved.cross = 76;
    }
    if (moved.label === "WR" && moved.cross > 80) {
      moved.length = 68;
      moved.cross = 82;
    }
    if (moved.label === "SL") {
      moved.length = 69;
      moved.cross = 35;
    }
    if (moved.team === "defense" && moved.label.includes("LB")) {
      moved.length -= 3.5;
    }
    if (moved.team === "defense" && moved.label === "S" && moved.cross < 50) {
      moved.cross += 3;
      moved.length -= 2;
    }
    return moved;
  });

  const frame3 = clone(frame2);
  frame3.id = uid();
  frame3.name = "브레이크";
  frame3.objects = frame3.objects.map((object) => {
    if (object.kind !== "player") {
      return object;
    }
    const moved = clone(object);
    if (moved.label === "QB") {
      moved.length = 81;
      moved.cross = 47;
    }
    if (moved.label === "RB") {
      moved.length = 71;
      moved.cross = 41;
    }
    if (moved.label === "TE") {
      moved.length = 60;
      moved.cross = 64;
    }
    if (moved.label === "WR" && moved.cross < 20) {
      moved.length = 52;
      moved.cross = 28;
    }
    if (moved.label === "WR" && moved.cross > 80) {
      moved.length = 60;
      moved.cross = 74;
    }
    if (moved.label === "SL") {
      moved.length = 60;
      moved.cross = 46;
    }
    if (moved.team === "defense" && moved.label === "CB" && moved.cross < 30) {
      moved.cross = 25;
      moved.length = 58;
    }
    if (moved.team === "defense" && moved.label === "CB" && moved.cross > 70) {
      moved.cross = 77;
      moved.length = 60;
    }
    if (moved.team === "defense" && moved.label === "S") {
      moved.length = 55;
    }
    return moved;
  });

  return {
    version: 2,
    view: "half",
    frameDuration: 1400,
    playMeta: {
      ...defaultPlayMeta(),
      title: "Trips Right / Play Action",
      formation: "Trips Right",
      personnel: "11 Personnel",
      down: 1,
      distance: 10,
      ballOn: 17,
      hash: "middle",
      notes: "오버와 슬랜트로 2단 레벨을 만들고, 체크다운으로 RB를 남겨둔 샘플 플레이.",
      tags: "demo, play-action, trips",
    },
    layers: defaultLayers(),
    viewOptions: defaultViewOptions(),
    currentFrameIndex: 0,
    frames: [frame1, frame2, frame3].map((frame) => ensureSingleBall(frame)),
  };
}

function getProjectData() {
  return {
    version: 2,
    view: state.view,
    routeColor: state.routeColor,
    routeLineStyle: state.routeLineStyle,
    frameDuration: state.frameDuration,
    playMeta: state.playMeta,
    layers: state.layers,
    viewOptions: state.viewOptions,
    currentFrameIndex: state.currentFrameIndex,
    frames: state.frames,
  };
}

function applyProjectData(project) {
  stopPlayback(false);
  state.view = project.view in FIELD_PRESETS ? project.view : "half";
  state.routeColor =
    typeof project.routeColor === "string" ? project.routeColor : TEAM_COLORS.offense;
  state.routeLineStyle = ["solid", "dashed", "motion"].includes(project.routeLineStyle)
    ? project.routeLineStyle
    : "solid";
  state.frameDuration = clamp(project.frameDuration || 1400, 500, 3000);
  state.frames = Array.isArray(project.frames) && project.frames.length
    ? normalizeFrames(clone(project.frames))
    : buildDemoProject().frames;
  state.playMeta = normalizePlayMeta(project.playMeta, state.frames);
  state.layers = normalizeLayers(project.layers);
  state.viewOptions = normalizeViewOptions(project.viewOptions);
  state.currentFrameIndex = clamp(
    project.currentFrameIndex || 0,
    0,
    state.frames.length - 1,
  );
  state.selectedId = null;
  ui.pendingPath = [];
  ui.zoneDraft = null;
  ui.snapGuides = [];
}

function pushHistory() {
  const snapshot = clone(getProjectData());
  const encoded = JSON.stringify(snapshot);
  const current = ui.history[ui.historyIndex];
  if (current && current.encoded === encoded) {
    return;
  }

  ui.history = ui.history.slice(0, ui.historyIndex + 1);
  ui.history.push({ encoded, snapshot });

  if (ui.history.length > MAX_HISTORY) {
    ui.history.shift();
  } else {
    ui.historyIndex += 1;
  }

  if (ui.history.length === MAX_HISTORY) {
    ui.historyIndex = ui.history.length - 1;
  }
}

function persistProject() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(getProjectData()));
    ui.lastSavedAt = new Date();
  } catch (error) {
    console.error("프로젝트 저장 실패", error);
  }
}

function commitProject() {
  state.frames = normalizeFrames(state.frames);
  pushHistory();
  persistProject();
  renderAll();
}

function loadProjectFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    if (!parsed || !Array.isArray(parsed.frames) || !parsed.frames.length) {
      return null;
    }
    return parsed;
  } catch (error) {
    console.error("저장된 프로젝트를 읽지 못했습니다.", error);
    return null;
  }
}

function getCurrentFrame() {
  return state.frames[state.currentFrameIndex];
}

function getFrameByIndex(index) {
  return state.frames[index];
}

function findObject(id, frame = getCurrentFrame()) {
  return frame?.objects.find((object) => object.id === id) || null;
}

function updateObject(id, updater) {
  const frame = getCurrentFrame();
  if (!frame) {
    return;
  }
  frame.objects = frame.objects.map((object) =>
    object.id === id ? updater(clone(object)) : object,
  );
}

function deleteObject(id) {
  const frame = getCurrentFrame();
  if (!frame) {
    return;
  }
  frame.objects = frame.objects.filter((object) => object.id !== id);
  if (state.selectedId === id) {
    state.selectedId = null;
  }
}

function currentPreset() {
  return FIELD_PRESETS[state.view];
}

function mapPoint(cross, length, preset = currentPreset()) {
  const { fieldRect, orientation } = preset;
  if (orientation === "vertical") {
    return {
      x: fieldRect.x + (fieldRect.width * cross) / 100,
      y: fieldRect.y + (fieldRect.height * length) / 100,
    };
  }

  return {
    x: fieldRect.x + (fieldRect.width * (100 - length)) / 100,
    y: fieldRect.y + (fieldRect.height * cross) / 100,
  };
}

function mapRect(cross, length, crossSize, lengthSize, preset = currentPreset()) {
  const { fieldRect, orientation } = preset;
  if (orientation === "vertical") {
    const origin = mapPoint(cross, length, preset);
    return {
      x: origin.x,
      y: origin.y,
      width: (fieldRect.width * crossSize) / 100,
      height: (fieldRect.height * lengthSize) / 100,
    };
  }

  return {
    x: fieldRect.x + (fieldRect.width * (100 - length - lengthSize)) / 100,
    y: fieldRect.y + (fieldRect.height * cross) / 100,
    width: (fieldRect.width * lengthSize) / 100,
    height: (fieldRect.height * crossSize) / 100,
  };
}

function screenToField(event) {
  const ctm = refs.board.getScreenCTM();
  if (!ctm) {
    return null;
  }
  const point = refs.board.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  const local = point.matrixTransform(ctm.inverse());
  const preset = currentPreset();
  const { fieldRect, orientation } = preset;

  let cross;
  let length;

  if (orientation === "vertical") {
    cross = ((local.x - fieldRect.x) / fieldRect.width) * 100;
    length = ((local.y - fieldRect.y) / fieldRect.height) * 100;
  } else {
    length = (1 - (local.x - fieldRect.x) / fieldRect.width) * 100;
    cross = ((local.y - fieldRect.y) / fieldRect.height) * 100;
  }

  return {
    cross: clamp(round(cross), 0, 100),
    length: clamp(round(length), 0, 100),
  };
}

function canPanViewport() {
  return state.zoom > 1.001;
}

function canDragFieldViewport() {
  return state.tool === "select" && !ui.playing && canPanViewport();
}

function syncBoardInteractionState() {
  refs.board.classList.toggle("is-pannable", canDragFieldViewport());
  refs.board.classList.toggle("is-panning", Boolean(ui.panDrag));
}

function getBoardViewBox(preset = currentPreset()) {
  const zoom = clamp(state.zoom || 1, 1, 3);
  const width = preset.viewBox.width / zoom;
  const height = preset.viewBox.height / zoom;
  const maxPanX = Math.max(0, (preset.viewBox.width - width) / 2);
  const maxPanY = Math.max(0, (preset.viewBox.height - height) / 2);
  const panX = clamp(state.panX || 0, -maxPanX, maxPanX);
  const panY = clamp(state.panY || 0, -maxPanY, maxPanY);
  return {
    x: round((preset.viewBox.width - width) / 2 + panX),
    y: round((preset.viewBox.height - height) / 2 + panY),
    width: round(width),
    height: round(height),
  };
}

function getPanBounds(preset = currentPreset(), zoom = state.zoom || 1) {
  const normalizedZoom = clamp(zoom, 1, 3);
  return {
    maxX: Math.max(0, (preset.viewBox.width - preset.viewBox.width / normalizedZoom) / 2),
    maxY: Math.max(0, (preset.viewBox.height - preset.viewBox.height / normalizedZoom) / 2),
  };
}

function endzoneRects(preset, goalStartPercent) {
  if (preset.orientation === "vertical") {
    return [
      mapRect(0, 0, 100, goalStartPercent, preset),
      mapRect(0, 100 - goalStartPercent, 100, goalStartPercent, preset),
    ];
  }

  return [
    mapRect(0, 100 - goalStartPercent, 100, goalStartPercent, preset),
    mapRect(0, 0, 100, goalStartPercent, preset),
  ];
}

function buildWatermark(rect, orientation, side) {
  const centerX = rect.x + rect.width / 2;
  const centerY = rect.y + rect.height / 2;
  const isSideEndzone = orientation === "horizontal";
  const major = isSideEndzone ? rect.height : rect.width;
  const minor = isSideEndzone ? rect.width : rect.height;
  const rotation = isSideEndzone ? (side === "start" ? -90 : 90) : 0;
  const textLength = round(major * 0.52);
  const fontSize = round(Math.min(minor * 0.28, major * 0.08, 24));
  return `
    <text
      x="${centerX}"
      y="${centerY}"
      fill="#ffffff"
      fill-opacity="0.14"
      font-size="${fontSize}"
      font-weight="700"
      letter-spacing="1.2"
      font-family="Space Grotesk, IBM Plex Sans KR, Pretendard, sans-serif"
      text-anchor="middle"
      dominant-baseline="middle"
      lengthAdjust="spacingAndGlyphs"
      textLength="${textLength}"
      ${rotation ? `transform="rotate(${rotation} ${centerX} ${centerY})"` : ""}
    >@nfldictionary</text>
  `;
}

function buildFieldMarkup() {
  const preset = currentPreset();
  const { viewBox, fieldRect, orientation, visibleYards, endzoneYards } = preset;
  const goalStartPercent = (endzoneYards / visibleYards) * 100;
  const fullScaleX = fieldRect.width / FIELD_ART.innerWidth;
  const fullScaleY = fieldRect.height / FIELD_ART.innerHeight;
  const fullArtRect = {
    x: fieldRect.x - FIELD_ART.innerX * fullScaleX,
    y: fieldRect.y - FIELD_ART.innerY * fullScaleY,
    width: FIELD_ART.fullWidth * fullScaleX,
    height: FIELD_ART.fullHeight * fullScaleY,
  };
  const verticalScaleX = fieldRect.width / FIELD_ART.innerHeight;
  const verticalScaleY = fieldRect.height / FIELD_ART.innerWidth;
  const verticalMatrix = {
    a: 0,
    b: -verticalScaleY,
    c: verticalScaleX,
    d: 0,
    e: fieldRect.x - verticalScaleX * FIELD_ART.innerY,
    f: fieldRect.y + fieldRect.height + verticalScaleY * FIELD_ART.innerX,
  };
  const [endzoneStart, endzoneFinish] = endzoneRects(preset, goalStartPercent);
  const fullFieldBackground = `
    <image
      href="${FIELD_ART.href}"
      xlink:href="${FIELD_ART.href}"
      x="${fullArtRect.x}"
      y="${fullArtRect.y}"
      width="${fullArtRect.width}"
      height="${fullArtRect.height}"
      preserveAspectRatio="none"
    />
  `;
  const halfFieldBackground = `
    <image
      href="${FIELD_ART.href}"
      xlink:href="${FIELD_ART.href}"
      x="0"
      y="0"
      width="${FIELD_ART.fullWidth}"
      height="${FIELD_ART.fullHeight}"
      transform="matrix(${verticalMatrix.a} ${verticalMatrix.b} ${verticalMatrix.c} ${verticalMatrix.d} ${verticalMatrix.e} ${verticalMatrix.f})"
      preserveAspectRatio="none"
    />
  `;
  const watermarkStart = buildWatermark(
    endzoneStart,
    orientation,
    "start",
  );
  const watermarkFinish = buildWatermark(
    endzoneFinish,
    orientation,
    "finish",
  );

  return `
    <svg
      xmlns="${SVG_NS}"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      viewBox="0 0 ${viewBox.width} ${viewBox.height}"
      fill="none"
    >
      <defs>
        <marker
          id="arrowHead"
          viewBox="0 0 14 14"
          markerWidth="14"
          markerHeight="14"
          refX="12"
          refY="7"
          orient="auto"
          markerUnits="userSpaceOnUse"
        >
          <path d="M0 0 L10 7 L0 14 Z" fill="context-stroke" />
        </marker>
      </defs>

      <rect width="${viewBox.width}" height="${viewBox.height}" fill="#ffffff" />
      ${orientation === "horizontal" ? fullFieldBackground : halfFieldBackground}
      <rect
        x="${fieldRect.x}"
        y="${fieldRect.y}"
        width="${fieldRect.width}"
        height="${fieldRect.height}"
        fill="none"
        stroke="rgba(255,255,255,0.28)"
        stroke-width="2"
      />
      ${watermarkStart}
      ${watermarkFinish}
      <rect
        class="field-surface"
        data-field-surface="true"
        x="${fieldRect.x}"
        y="${fieldRect.y}"
        width="${fieldRect.width}"
        height="${fieldRect.height}"
      />
    </svg>
  `;
}

function renderPlayer(object, options = {}) {
  const point = mapPoint(object.cross, object.length);
  const radius = object.size === "small" ? 12.8 : 18.4;
  const interactive = options.interactive !== false;
  const isSelected = interactive && (options.selectedId ?? state.selectedId) === object.id;
  const fill = object.color || teamColor(object.team);
  const outline = object.team === "neutral" ? "#1e1e1e" : "rgba(255,255,255,0.95)";
  return `
    <g
      ${interactive ? `data-object-id="${object.id}"` : ""}
      data-kind="player"
      transform="translate(${point.x} ${point.y}) rotate(${object.rotation})"
      opacity="${options.opacity ?? 1}"
      style="${interactive ? "cursor: grab;" : "pointer-events: none;"}"
    >
      ${
        isSelected
          ? `<circle r="${radius + 6}" fill="none" stroke="#ffd166" stroke-width="4" />`
          : ""
      }
      <circle
        r="${radius}"
        fill="${fill}"
        stroke="${outline}"
        stroke-width="2.5"
      />
      <text
        x="0"
        y="${object.number ? -1.5 : 3.5}"
        fill="#ffffff"
        font-size="${object.size === "small" ? 8.8 : 10.4}"
        font-weight="700"
        text-anchor="middle"
        dominant-baseline="middle"
        pointer-events="none"
      >${escapeHtml(object.label)}</text>
      ${
        object.number
          ? `
        <text
          x="0"
          y="9"
          fill="rgba(255,255,255,0.92)"
          font-size="7.2"
          font-weight="600"
          text-anchor="middle"
          dominant-baseline="middle"
          pointer-events="none"
        >${escapeHtml(object.number)}</text>
      `
          : ""
      }
    </g>
  `;
}

function renderBall(object, options = {}) {
  const point = mapPoint(object.cross, object.length);
  const interactive = options.interactive !== false;
  const isSelected = interactive && (options.selectedId ?? state.selectedId) === object.id;
  const scale = object.scale ?? 1;
  const halfWidth = BALL_ART.width / 2;
  const halfHeight = BALL_ART.height / 2;
  return `
    <g
      ${interactive ? `data-object-id="${object.id}"` : ""}
      data-kind="ball"
      transform="translate(${point.x} ${point.y}) rotate(${object.rotation}) scale(${scale})"
      opacity="${options.opacity ?? 1}"
      style="${interactive ? "cursor: grab;" : "pointer-events: none;"}"
    >
      ${
        isSelected
          ? `<ellipse rx="${halfWidth + 3}" ry="${halfHeight + 3}" fill="none" stroke="#ffd166" stroke-width="3" />`
          : ""
      }
      <image
        href="${BALL_ART.href}"
        xlink:href="${BALL_ART.href}"
        x="${-halfWidth}"
        y="${-halfHeight}"
        width="${BALL_ART.width}"
        height="${BALL_ART.height}"
        preserveAspectRatio="xMidYMid meet"
      />
    </g>
  `;
}

function renderPath(object, options = {}) {
  const points = object.points.map((point) => mapPoint(point.cross, point.length));
  const line = points.map((point) => `${point.x},${point.y}`).join(" ");
  const interactive = options.interactive !== false;
  const isSelected = interactive && (options.selectedId ?? state.selectedId) === object.id;
  const labelPoint = points[Math.max(0, Math.floor(points.length / 2) - 1)];
  const strokeDashArray = strokeDashArrayForPath(object);
  return `
    <g ${interactive ? `data-object-id="${object.id}"` : ""} data-kind="path" opacity="${options.opacity ?? 1}" style="${interactive ? "cursor: grab;" : "pointer-events: none;"}">
      ${
        isSelected
          ? `<polyline
              points="${line}"
              fill="none"
              stroke="#ffd166"
              stroke-width="${object.width + 8}"
              stroke-linecap="round"
              stroke-linejoin="round"
              opacity="0.28"
            />`
          : ""
      }
      <polyline
        points="${line}"
        fill="none"
        stroke="${object.color}"
        stroke-width="${object.width}"
        stroke-linecap="${strokeLinecapForPath(object)}"
        stroke-linejoin="round"
        stroke-dasharray="${strokeDashArray}"
        marker-end="${object.arrow ? "url(#arrowHead)" : ""}"
        opacity="${object.opacity ?? 1}"
      />
      ${
        object.label && labelPoint
          ? `
        <text
          x="${labelPoint.x + 8}"
          y="${labelPoint.y - 10}"
          fill="${object.color}"
          font-size="16"
          font-weight="700"
        >${escapeHtml(object.label)}</text>
      `
          : ""
      }
    </g>
  `;
}

function renderZone(object, options = {}) {
  const rect = mapRect(
    object.cross,
    object.length,
    object.crossSize,
    object.lengthSize,
  );
  const center = {
    x: rect.x + rect.width / 2,
    y: rect.y + rect.height / 2,
  };
  const interactive = options.interactive !== false;
  const isSelected = interactive && (options.selectedId ?? state.selectedId) === object.id;
  const shape =
    object.shape === "ellipse"
      ? `<ellipse
          cx="${center.x}"
          cy="${center.y}"
          rx="${rect.width / 2}"
          ry="${rect.height / 2}"
          fill="${object.color}"
          fill-opacity="${object.opacity}"
          stroke="${object.color}"
          stroke-width="3"
          stroke-dasharray="12 10"
        />`
      : `<rect
          x="${rect.x}"
          y="${rect.y}"
          width="${rect.width}"
          height="${rect.height}"
          fill="${object.color}"
          fill-opacity="${object.opacity}"
          stroke="${object.color}"
          stroke-width="3"
          stroke-dasharray="12 10"
        />`;

  return `
    <g ${interactive ? `data-object-id="${object.id}"` : ""} data-kind="zone" opacity="${options.opacity ?? 1}" style="${interactive ? "cursor: grab;" : "pointer-events: none;"}">
      ${shape}
      ${
        isSelected
          ? `<rect
              x="${rect.x - 6}"
              y="${rect.y - 6}"
              width="${rect.width + 12}"
              height="${rect.height + 12}"
              fill="none"
              stroke="#ffd166"
              stroke-width="3"
              stroke-dasharray="10 8"
            />`
          : ""
      }
      ${
        object.label
          ? `<text
              x="${center.x}"
              y="${center.y}"
              fill="#ffffff"
              font-size="16"
              font-weight="700"
              text-anchor="middle"
              dominant-baseline="middle"
            >${escapeHtml(object.label)}</text>`
          : ""
      }
    </g>
  `;
}

function renderTextObject(object, options = {}) {
  const point = mapPoint(object.cross, object.length);
  const interactive = options.interactive !== false;
  const isSelected = interactive && (options.selectedId ?? state.selectedId) === object.id;
  return `
    <g ${interactive ? `data-object-id="${object.id}"` : ""} data-kind="text" opacity="${options.opacity ?? 1}" style="${interactive ? "cursor: grab;" : "pointer-events: none;"}">
      ${
        isSelected
          ? `<circle cx="${point.x}" cy="${point.y}" r="20" fill="rgba(255,209,102,0.2)" stroke="#ffd166" stroke-width="3" />`
          : ""
      }
      <text
        x="${point.x}"
        y="${point.y}"
        fill="${object.color}"
        font-size="${object.fontSize}"
        font-weight="700"
        text-anchor="${object.align}"
      >${escapeHtml(object.text)}</text>
    </g>
  `;
}

function renderObjectMarkup(object, options = {}) {
  if (!isObjectVisible(object)) {
    return "";
  }
  if (object.kind === "player") {
    return renderPlayer(object, options);
  }
  if (object.kind === "ball") {
    return renderBall(object, options);
  }
  if (object.kind === "path") {
    return renderPath(object, options);
  }
  if (object.kind === "zone") {
    return renderZone(object, options);
  }
  if (object.kind === "text") {
    return renderTextObject(object, options);
  }
  return "";
}

function renderFrameObjects(frame, options = {}) {
  return frame.objects.map((object) => renderObjectMarkup(object, options)).join("");
}

function renderSystemMarkers() {
  if (!isLayerVisible("markers")) {
    return "";
  }
  const markers = driveMarkers(state.playMeta)
    .map((object) => renderPath(object, { interactive: false, selectedId: null, opacity: 0.94 }))
    .join("");
  const hashCross = HASH_CROSS[state.playMeta.hash] ?? HASH_CROSS.middle;
  const losLength = driveMarkers(state.playMeta)[0].points[0].length;
  const spot = mapPoint(hashCross, losLength);
  return markers + `
    <g opacity="0.95" pointer-events="none">
      <circle cx="${spot.x}" cy="${spot.y}" r="8" fill="#ffffff" stroke="#1f7a3f" stroke-width="3" />
      <text x="${spot.x}" y="${spot.y + 1}" fill="#1f7a3f" font-size="10" font-weight="700" text-anchor="middle" dominant-baseline="middle">
        ${escapeHtml(state.playMeta.hash === "middle" ? "M" : state.playMeta.hash === "left" ? "L" : "R")}
      </text>
    </g>
  `;
}

function renderOnionSkin() {
  if (ui.playing || !state.viewOptions.onionSkin) {
    return "";
  }
  const fragments = [];
  const previous = getFrameByIndex(state.currentFrameIndex - 1);
  const next = getFrameByIndex(state.currentFrameIndex + 1);
  if (previous) {
    fragments.push(`<g opacity="0.18">${renderFrameObjects(previous, {
      interactive: false,
      selectedId: null,
    })}</g>`);
  }
  if (next) {
    fragments.push(`<g opacity="0.14">${renderFrameObjects(next, {
      interactive: false,
      selectedId: null,
    })}</g>`);
  }
  return fragments.join("");
}

function renderPendingDrafts() {
  const fragments = [];

  if (ui.zoneDraft) {
    const cross = Math.min(ui.zoneDraft.start.cross, ui.zoneDraft.current.cross);
    const length = Math.min(ui.zoneDraft.start.length, ui.zoneDraft.current.length);
    const crossSize = Math.abs(ui.zoneDraft.start.cross - ui.zoneDraft.current.cross);
    const lengthSize = Math.abs(ui.zoneDraft.start.length - ui.zoneDraft.current.length);
    const rect = mapRect(cross, length, crossSize, lengthSize);
    const draftColor = ui.zoneDraft.overrides?.color || "#ffd166";
    const draftOpacity = ui.zoneDraft.overrides?.opacity ?? 0.18;
    if (ui.zoneDraft.overrides?.shape === "ellipse") {
      fragments.push(`
        <ellipse
          cx="${rect.x + rect.width / 2}"
          cy="${rect.y + rect.height / 2}"
          rx="${rect.width / 2}"
          ry="${rect.height / 2}"
          fill="${draftColor}"
          fill-opacity="${draftOpacity}"
          stroke="${draftColor}"
          stroke-width="3"
          stroke-dasharray="10 10"
        />
      `);
    } else {
      fragments.push(`
        <rect
          x="${rect.x}"
          y="${rect.y}"
          width="${rect.width}"
          height="${rect.height}"
          fill="${draftColor}"
          fill-opacity="${draftOpacity}"
          stroke="${draftColor}"
          stroke-width="3"
          stroke-dasharray="10 10"
        />
      `);
    }
  }

  if (ui.pendingPath.length) {
    const previewPoints = [...ui.pendingPath];
    if (ui.pointerField) {
      previewPoints.push(ui.pointerField);
    }
    const mapped = previewPoints.map((point) => mapPoint(point.cross, point.length));
    const selected = findObject(state.selectedId);
    const previewStyle = pathStyleForTool(state.tool, selected);
    fragments.push(`
      <polyline
        points="${mapped.map((point) => `${point.x},${point.y}`).join(" ")}"
        fill="none"
        stroke="${previewStyle.color}"
        stroke-width="${previewStyle.width}"
        stroke-linecap="${strokeLinecapForPath(previewStyle)}"
        stroke-linejoin="round"
        stroke-dasharray="${strokeDashArrayForPath(previewStyle)}"
        marker-end="${previewStyle.arrow ? "url(#arrowHead)" : ""}"
        opacity="${previewStyle.opacity ?? 1}"
      />
    `);
    previewPoints.slice(0, Math.max(0, previewPoints.length - 1)).forEach((point) => {
      const mappedPoint = mapPoint(point.cross, point.length);
      fragments.push(`
        <circle
          cx="${mappedPoint.x}"
          cy="${mappedPoint.y}"
          r="7"
          fill="#ffd166"
          stroke="rgba(0,0,0,0.4)"
          stroke-width="2"
        />
      `);
    });
  }

  ui.snapGuides.forEach((guide, index) => {
    fragments.push(`
      <line
        key="snap-${index}"
        class="guide-line ${guide.axis === "cross" ? "guide-line--secondary" : ""}"
        x1="${guide.x1}"
        y1="${guide.y1}"
        x2="${guide.x2}"
        y2="${guide.y2}"
      />
    `);
  });

  return fragments.join("");
}

function interpolateNumber(a, b, t) {
  return a + (b - a) * t;
}

function interpolateObject(objectA, objectB, t) {
  if (!objectA && !objectB) {
    return null;
  }
  if (!objectA) {
    return t < 0.55 ? null : clone(objectB);
  }
  if (!objectB) {
    return t < 0.45 ? clone(objectA) : null;
  }
  if (objectA.kind !== objectB.kind) {
    return t < 0.5 ? clone(objectA) : clone(objectB);
  }

  if (objectA.kind === "player") {
    return {
      ...clone(objectA),
      cross: interpolateNumber(objectA.cross, objectB.cross, t),
      length: interpolateNumber(objectA.length, objectB.length, t),
      rotation: interpolateNumber(objectA.rotation, objectB.rotation, t),
    };
  }

  if (objectA.kind === "ball") {
    return {
      ...clone(objectA),
      cross: interpolateNumber(objectA.cross, objectB.cross, t),
      length: interpolateNumber(objectA.length, objectB.length, t),
      rotation: interpolateNumber(objectA.rotation ?? -18, objectB.rotation ?? -18, t),
      scale: interpolateNumber(objectA.scale ?? 1, objectB.scale ?? 1, t),
    };
  }

  if (objectA.kind === "text") {
    return {
      ...clone(objectA),
      cross: interpolateNumber(objectA.cross, objectB.cross, t),
      length: interpolateNumber(objectA.length, objectB.length, t),
      fontSize: interpolateNumber(objectA.fontSize, objectB.fontSize, t),
    };
  }

  if (objectA.kind === "zone") {
    return {
      ...clone(objectA),
      cross: interpolateNumber(objectA.cross, objectB.cross, t),
      length: interpolateNumber(objectA.length, objectB.length, t),
      crossSize: interpolateNumber(objectA.crossSize, objectB.crossSize, t),
      lengthSize: interpolateNumber(objectA.lengthSize, objectB.lengthSize, t),
      opacity: interpolateNumber(objectA.opacity, objectB.opacity, t),
    };
  }

  if (
    objectA.kind === "path" &&
    objectA.points.length === objectB.points.length
  ) {
    return {
      ...clone(objectA),
      points: objectA.points.map((point, index) => ({
        cross: interpolateNumber(point.cross, objectB.points[index].cross, t),
        length: interpolateNumber(point.length, objectB.points[index].length, t),
      })),
      width: interpolateNumber(objectA.width, objectB.width, t),
      opacity: interpolateNumber(objectA.opacity, objectB.opacity, t),
    };
  }

  return t < 0.5 ? clone(objectA) : clone(objectB);
}

function getRenderableFrame() {
  if (!ui.preview) {
    return getCurrentFrame();
  }

  const frameA = getFrameByIndex(ui.preview.from);
  const frameB = getFrameByIndex(ui.preview.to);
  if (!frameA || !frameB) {
    return getCurrentFrame();
  }

  const mapA = new Map(frameA.objects.map((object) => [object.id, object]));
  const mapB = new Map(frameB.objects.map((object) => [object.id, object]));
  const order = [
    ...frameA.objects.map((object) => object.id),
    ...frameB.objects
      .map((object) => object.id)
      .filter((id) => !mapA.has(id)),
  ];

  return {
    id: `preview-${frameA.id}-${frameB.id}`,
    name: "preview",
    objects: order
      .map((id) => interpolateObject(mapA.get(id), mapB.get(id), ui.preview.t))
      .filter(Boolean),
  };
}

function renderBoard() {
  const preset = currentPreset();
  const boardViewBox = getBoardViewBox(preset);
  const fieldSvg = buildFieldMarkup();
  refs.board.setAttribute(
    "viewBox",
    `${boardViewBox.x} ${boardViewBox.y} ${boardViewBox.width} ${boardViewBox.height}`,
  );
  refs.board.setAttribute("preserveAspectRatio", "xMidYMid meet");

  const frame = getRenderableFrame();
  const objectsMarkup = renderFrameObjects(frame);

  const inner = new DOMParser().parseFromString(fieldSvg, "image/svg+xml").documentElement;
  refs.board.innerHTML = inner.innerHTML +
    renderOnionSkin() +
    renderSystemMarkers() +
    objectsMarkup +
    renderPendingDrafts();
  syncBoardInteractionState();
}

function renderFrameStrip() {
  refs.frameStrip.innerHTML = state.frames
    .map((frame, index) => {
      const players = frame.objects.filter((object) => object.kind === "player").length;
      const balls = frame.objects.filter((object) => object.kind === "ball").length;
      const drawings = frame.objects.length - players - balls;
      return `
        <button
          class="frame-card ${index === state.currentFrameIndex ? "is-active" : ""}"
          data-frame-index="${index}"
        >
          <strong>${index + 1}. ${escapeHtml(frame.name || `프레임 ${index + 1}`)}</strong>
          <small>선수 ${players}명 · 공 ${balls}개 · 도형/라우트 ${drawings}개</small>
        </button>
      `;
    })
    .join("");
}

function renderPlaySettings() {
  refs.playSettingsPanel.innerHTML = `
    <div class="meta-grid">
      <div class="field-row field-row--full">
        <label>플레이 제목</label>
        <input data-play-field="title" type="text" value="${escapeHtml(state.playMeta.title)}" />
      </div>
      <div class="field-row">
        <label>포메이션</label>
        <input data-play-field="formation" type="text" value="${escapeHtml(state.playMeta.formation)}" />
      </div>
      <div class="field-row">
        <label>퍼스널</label>
        <input data-play-field="personnel" type="text" value="${escapeHtml(state.playMeta.personnel)}" />
      </div>
      <div class="field-row">
        <label>다운</label>
        <select data-play-field="down">
          <option value="1" ${state.playMeta.down === 1 ? "selected" : ""}>1st</option>
          <option value="2" ${state.playMeta.down === 2 ? "selected" : ""}>2nd</option>
          <option value="3" ${state.playMeta.down === 3 ? "selected" : ""}>3rd</option>
          <option value="4" ${state.playMeta.down === 4 ? "selected" : ""}>4th</option>
        </select>
      </div>
      <div class="field-row">
        <label>거리</label>
        <div class="field-inline">
          <input data-play-field="distance" data-type="number" type="range" min="1" max="40" value="${state.playMeta.distance}" />
          <strong data-play-display="distance">${state.playMeta.distance} yd</strong>
        </div>
      </div>
      <div class="field-row">
        <label>볼 위치</label>
        <div class="field-inline">
          <input data-play-field="ballOn" data-type="number" type="range" min="1" max="99" value="${state.playMeta.ballOn}" />
          <strong data-play-display="ballOn">${ballOnLabel(state.playMeta.ballOn)}</strong>
        </div>
      </div>
      <div class="field-row">
        <label>해시</label>
        <select data-play-field="hash">
          <option value="left" ${state.playMeta.hash === "left" ? "selected" : ""}>Left</option>
          <option value="middle" ${state.playMeta.hash === "middle" ? "selected" : ""}>Middle</option>
          <option value="right" ${state.playMeta.hash === "right" ? "selected" : ""}>Right</option>
        </select>
      </div>
      <div class="field-row field-row--full">
        <label>태그</label>
        <input data-play-field="tags" type="text" value="${escapeHtml(state.playMeta.tags)}" />
      </div>
      <div class="field-row field-row--full">
        <label>노트</label>
        <textarea data-play-field="notes">${escapeHtml(state.playMeta.notes)}</textarea>
      </div>
    </div>
    <p class="panel-mini-note">LOS/1ST 기준선은 여기의 다운·거리·볼 위치를 기준으로 자동 갱신됩니다.</p>
  `;
}

function renderLayerPanel() {
  refs.layerPanel.innerHTML = `
    <div class="layer-list">
      ${LAYER_DEFS.map((definition) => `
        <div class="layer-row">
          <strong>${definition.label}</strong>
          <label class="layer-toggle">
            <input
              data-layer-key="${definition.key}"
              data-layer-field="visible"
              type="checkbox"
              ${state.layers[definition.key]?.visible !== false ? "checked" : ""}
            />
            표시
          </label>
          <label class="layer-toggle">
            <input
              data-layer-key="${definition.key}"
              data-layer-field="locked"
              type="checkbox"
              ${state.layers[definition.key]?.locked === true ? "checked" : ""}
            />
            잠금
          </label>
        </div>
      `).join("")}
    </div>
    <p class="panel-mini-note">잠금된 레이어는 보이더라도 이동·수정되지 않습니다.</p>
  `;
}

function renderInspector() {
  const selected = findObject(state.selectedId);
  if (selected && !isObjectVisible(selected)) {
    state.selectedId = null;
    return renderInspector();
  }
  if (!selected) {
    refs.inspectorContent.innerHTML = `
      <div class="empty-state">
        보드에서 오브젝트를 선택하면 위치, 라벨, 색상, 크기, 투명도 등을 바로
        조정할 수 있습니다.
      </div>
    `;
    return;
  }

  if (isObjectLocked(selected)) {
    refs.inspectorContent.innerHTML = `
      <div class="empty-state">
        현재 선택한 오브젝트는 잠금 레이어에 있습니다. 우측의 레이어 패널에서 잠금을
        해제하면 편집할 수 있습니다.
      </div>
    `;
    return;
  }

  if (selected.kind === "player") {
    refs.inspectorContent.innerHTML = `
      <div class="field-row">
        <label>라벨</label>
        <input data-field="label" type="text" value="${escapeHtml(selected.label)}" />
      </div>
      <div class="field-row">
        <label>번호</label>
        <input data-field="number" type="text" value="${escapeHtml(selected.number)}" />
      </div>
      <div class="field-row">
        <label>팀</label>
        <select data-field="team">
          <option value="offense" ${selected.team === "offense" ? "selected" : ""}>공격</option>
          <option value="defense" ${selected.team === "defense" ? "selected" : ""}>수비</option>
          <option value="neutral" ${selected.team === "neutral" ? "selected" : ""}>중립</option>
        </select>
      </div>
      <div class="field-row">
        <label>칩 크기</label>
        <select data-field="size">
          <option value="large" ${selected.size === "large" ? "selected" : ""}>큰 칩</option>
          <option value="small" ${selected.size === "small" ? "selected" : ""}>작은 칩</option>
        </select>
      </div>
      <div class="field-row">
        <label>색상</label>
        <input data-field="color" type="color" value="${selected.color}" />
      </div>
      <div class="field-row">
        <label>회전</label>
        <input data-field="rotation" data-type="number" type="range" min="-180" max="180" value="${selected.rotation}" />
      </div>
      <div class="field-row">
        <label>가로 위치(%)</label>
        <input data-field="cross" data-type="number" type="number" min="0" max="100" step="0.1" value="${selected.cross}" />
      </div>
      <div class="field-row">
        <label>길이 위치(%)</label>
        <input data-field="length" data-type="number" type="number" min="0" max="100" step="0.1" value="${selected.length}" />
      </div>
    `;
    return;
  }

  if (selected.kind === "ball") {
    refs.inspectorContent.innerHTML = `
      <div class="field-row">
        <label>회전</label>
        <input data-field="rotation" data-type="number" type="range" min="-180" max="180" value="${selected.rotation ?? -18}" />
      </div>
      <div class="field-row">
        <label>크기</label>
        <input data-field="scale" data-type="number" type="range" min="0.6" max="1.6" step="0.05" value="${selected.scale ?? 1}" />
      </div>
      <div class="field-row">
        <label>가로 위치(%)</label>
        <input data-field="cross" data-type="number" type="number" min="0" max="100" step="0.1" value="${selected.cross}" />
      </div>
      <div class="field-row">
        <label>길이 위치(%)</label>
        <input data-field="length" data-type="number" type="number" min="0" max="100" step="0.1" value="${selected.length}" />
      </div>
    `;
    return;
  }

  if (selected.kind === "path") {
    const lineStyle = resolvePathLineStyle(selected);
    refs.inspectorContent.innerHTML = `
      <div class="field-row">
        <label>라벨</label>
        <input data-field="label" type="text" value="${escapeHtml(selected.label || "")}" />
      </div>
      <div class="field-row">
        <label>색상</label>
        <input data-field="color" type="color" value="${selected.color}" />
      </div>
      <div class="field-row">
        <label>두께</label>
        <input data-field="width" data-type="number" type="range" min="1" max="12" step="0.2" value="${selected.width}" />
      </div>
      <div class="field-row">
        <label>화살표</label>
        <select data-field="arrow" data-type="boolean">
          <option value="true" ${selected.arrow ? "selected" : ""}>표시</option>
          <option value="false" ${!selected.arrow ? "selected" : ""}>숨김</option>
        </select>
      </div>
      <div class="field-row">
        <label>선 형태</label>
        <select data-field="lineStyle">
          <option value="solid" ${lineStyle === "solid" ? "selected" : ""}>실선</option>
          <option value="dashed" ${lineStyle === "dashed" ? "selected" : ""}>점선</option>
          <option value="motion" ${lineStyle === "motion" ? "selected" : ""}>모션 점선</option>
        </select>
      </div>
      <div class="field-row">
        <label>투명도</label>
        <input data-field="opacity" data-type="number" type="range" min="0.1" max="1" step="0.05" value="${selected.opacity}" />
      </div>
      <div class="empty-state">
        라우트 위치는 직접 드래그로 이동하거나, 프레임별로 새 라우트를 만들어서 다른
        상황을 표현하세요.
      </div>
    `;
    return;
  }

  if (selected.kind === "zone") {
    refs.inspectorContent.innerHTML = `
      <div class="field-row">
        <label>라벨</label>
        <input data-field="label" type="text" value="${escapeHtml(selected.label || "")}" />
      </div>
      <div class="field-row">
        <label>형태</label>
        <select data-field="shape">
          <option value="rect" ${selected.shape === "rect" ? "selected" : ""}>사각형</option>
          <option value="ellipse" ${selected.shape === "ellipse" ? "selected" : ""}>타원</option>
        </select>
      </div>
      <div class="field-row">
        <label>색상</label>
        <input data-field="color" type="color" value="${selected.color}" />
      </div>
      <div class="field-row">
        <label>투명도</label>
        <input data-field="opacity" data-type="number" type="range" min="0.05" max="0.8" step="0.05" value="${selected.opacity}" />
      </div>
      <div class="field-row">
        <label>가로 시작(%)</label>
        <input data-field="cross" data-type="number" type="number" min="0" max="100" step="0.1" value="${selected.cross}" />
      </div>
      <div class="field-row">
        <label>길이 시작(%)</label>
        <input data-field="length" data-type="number" type="number" min="0" max="100" step="0.1" value="${selected.length}" />
      </div>
      <div class="field-row">
        <label>가로 크기(%)</label>
        <input data-field="crossSize" data-type="number" type="number" min="1" max="100" step="0.1" value="${selected.crossSize}" />
      </div>
      <div class="field-row">
        <label>길이 크기(%)</label>
        <input data-field="lengthSize" data-type="number" type="number" min="1" max="100" step="0.1" value="${selected.lengthSize}" />
      </div>
    `;
    return;
  }

  refs.inspectorContent.innerHTML = `
    <div class="field-row">
      <label>텍스트</label>
      <textarea data-field="text">${escapeHtml(selected.text)}</textarea>
    </div>
    <div class="field-row">
      <label>색상</label>
      <input data-field="color" type="color" value="${selected.color}" />
    </div>
    <div class="field-row">
      <label>글자 크기</label>
      <input data-field="fontSize" data-type="number" type="range" min="12" max="56" value="${selected.fontSize}" />
    </div>
    <div class="field-row">
      <label>가로 위치(%)</label>
      <input data-field="cross" data-type="number" type="number" min="0" max="100" step="0.1" value="${selected.cross}" />
    </div>
    <div class="field-row">
      <label>길이 위치(%)</label>
      <input data-field="length" data-type="number" type="number" min="0" max="100" step="0.1" value="${selected.length}" />
    </div>
  `;
}

function renderProjectSummary() {
  const current = getCurrentFrame();
  const players = current.objects.filter((object) => object.kind === "player");
  const balls = current.objects.filter((object) => object.kind === "ball");
  const offenseCount = players.filter((object) => object.team === "offense").length;
  const defenseCount = players.filter((object) => object.team === "defense").length;
  const neutralCount = players.filter((object) => object.team === "neutral").length;
  const drawings = current.objects.length - players.length - balls.length;

  refs.projectSummary.innerHTML = `
    <div class="summary-card">
      <strong>플레이</strong>
      <p>${escapeHtml(state.playMeta.title)}</p>
    </div>
    <div class="summary-card">
      <strong>필드 템플릿</strong>
      <p>${FIELD_PRESETS[state.view].label}</p>
    </div>
    <div class="summary-card">
      <strong>다운 & 거리</strong>
      <p>${state.playMeta.down} down · ${state.playMeta.distance} yards · ${ballOnLabel(state.playMeta.ballOn)} · ${escapeHtml(state.playMeta.hash)}</p>
    </div>
    <div class="summary-card">
      <strong>현재 프레임</strong>
      <p>${state.currentFrameIndex + 1} / ${state.frames.length} · ${
        escapeHtml(current.name || `프레임 ${state.currentFrameIndex + 1}`)
      }</p>
    </div>
    <div class="summary-card">
      <strong>칩 분포</strong>
      <p>공격 ${offenseCount}/11 · 수비 ${defenseCount}/11 · 중립 ${neutralCount} · 공 ${balls.length}/1</p>
    </div>
    <div class="summary-card">
      <strong>드로잉 요소</strong>
      <p>라우트/영역/텍스트 ${drawings}개</p>
    </div>
    <div class="summary-card">
      <strong>메모</strong>
      <p>${escapeHtml(state.playMeta.notes || "메모 없음")}</p>
    </div>
  `;
}

function getTeamPlayerCount(team, frame = getCurrentFrame()) {
  return frame.objects.filter(
    (object) => object.kind === "player" && object.team === team,
  ).length;
}

function isAddLimitReached(team, frame = getCurrentFrame()) {
  if (team !== "offense" && team !== "defense") {
    return false;
  }
  return getTeamPlayerCount(team, frame) >= 11;
}

function renderToolbarState() {
  if (!TOOL_LABELS[state.tool]) {
    state.tool = "select";
  }

  document.querySelectorAll("[data-tool]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tool === state.tool);
    button.disabled = false;
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === state.view);
  });

  refs.modeLabel.textContent = TOOL_LABELS[state.tool];
  refs.routeStyleControls.hidden = !["path", "motion"].includes(state.tool);
  refs.routeColorInput.value = state.routeColor;
  refs.routeLineStyleSelect.value =
    state.tool === "motion" ? "motion" : state.routeLineStyle;
  refs.routeLineStyleSelect.disabled = state.tool === "motion";
  refs.snapToggleBtn.classList.toggle("is-active", state.viewOptions.snap);
  refs.onionSkinBtn.classList.toggle("is-active", state.viewOptions.onionSkin);
  refs.zoomRange.value = String(Math.round(state.zoom * 100));
  refs.zoomValue.textContent = `${Math.round(state.zoom * 100)}%`;
  refs.zoomOutBtn.disabled = state.zoom <= 1;
  refs.zoomInBtn.disabled = state.zoom >= 3;
  const panBounds = getPanBounds();
  const canPan = canPanViewport();
  refs.zoomResetBtn.disabled =
    Math.abs(state.zoom - 1) < 0.001 &&
    Math.abs(state.panX) < 0.01 &&
    Math.abs(state.panY) < 0.01;
  refs.panUpBtn.disabled = !canPan || state.panY <= -panBounds.maxY + 0.01;
  refs.panDownBtn.disabled = !canPan || state.panY >= panBounds.maxY - 0.01;
  refs.panLeftBtn.disabled = !canPan || state.panX <= -panBounds.maxX + 0.01;
  refs.panRightBtn.disabled = !canPan || state.panX >= panBounds.maxX - 0.01;
  refs.panCenterBtn.disabled = !canPan || (
    Math.abs(state.panX) < 0.01 && Math.abs(state.panY) < 0.01
  );
  refs.frameDurationRange.value = String(state.frameDuration);
  refs.frameDurationValue.textContent = `${(state.frameDuration / 1000).toFixed(1)}초`;
  refs.playBtn.textContent = ui.playing ? "일시정지" : "재생";
  refs.tweenFrameBtn.disabled = !getFrameByIndex(state.currentFrameIndex + 1);
  refs.finishPathBtn.disabled = ui.pendingPath.length < 2 || isLayerLocked("path");
  refs.cancelPathBtn.disabled = !ui.pendingPath.length;
  syncBoardInteractionState();

  const saveLabel = ui.lastSavedAt
    ? `브라우저 저장됨 · ${ui.lastSavedAt.toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
      })}`
    : "브라우저에 저장됨";
  refs.saveStateLabel.textContent = saveLabel;

  if (isLineDrawingTool(state.tool) && ui.pendingPath.length) {
    refs.boardHint.textContent = `경로 점 ${ui.pendingPath.length}개 · Enter로 완료, Esc로 취소`;
    return;
  }
  if (isLineDrawingTool(state.tool) && isLayerLocked("path")) {
    refs.boardHint.textContent = "경로 레이어 잠금을 해제하면 라우트/모션/블로킹을 그릴 수 있습니다.";
    return;
  }
  if (state.tool === "block") {
    refs.boardHint.textContent = "오펜스 블로킹 경로를 클릭으로 찍고 Enter로 마무리하세요.";
    return;
  }
  if (state.tool === "motion") {
    refs.boardHint.textContent = "프리스냅 모션이나 이동 방향을 점선 화살표로 표시하세요.";
    return;
  }
  if (state.tool === "rush") {
    refs.boardHint.textContent = "디펜스 패스러시 경로를 클릭으로 찍고 Enter로 마무리하세요.";
    return;
  }
  if (state.tool === "zone") {
    refs.boardHint.textContent = "드래그해서 수비 구역이나 스프레이 존을 그리세요.";
    return;
  }
  if (state.tool === "coverage") {
    refs.boardHint.textContent = "드래그해서 디펜스 커버리지 원형 영역을 그리세요.";
    return;
  }
  if (state.tool === "text") {
    refs.boardHint.textContent = "필드 클릭 후 텍스트를 입력하면 플레이북 메모를 남길 수 있습니다.";
    return;
  }
  if (state.tool === "select") {
    refs.boardHint.textContent = canPanViewport()
      ? "오브젝트를 드래그해 위치 조정, 빈 필드를 잡고 화면 이동"
      : "오브젝트를 드래그해 위치 조정, 우측 패널에서 세부 속성 편집";
    return;
  }
  if (state.tool === "offense") {
    refs.boardHint.textContent = "필드를 클릭해 공격 칩을 추가하세요.";
    return;
  }
  if (state.tool === "defense") {
    refs.boardHint.textContent = "필드를 클릭해 수비 칩을 추가하세요.";
    return;
  }
  if (state.tool === "neutral") {
    refs.boardHint.textContent = "필드를 클릭해 중립 칩을 추가하세요.";
    return;
  }
  if (state.tool === "ball") {
    refs.boardHint.textContent = "필드를 클릭하면 현재 프레임의 공 위치가 갱신됩니다.";
    return;
  }
  refs.boardHint.textContent = "필드를 클릭해 칩을 추가하세요.";
}

function renderAll() {
  renderBoard();
  renderFrameStrip();
  renderPlaySettings();
  renderLayerPanel();
  renderInspector();
  renderProjectSummary();
  renderToolbarState();
}

function setTool(tool) {
  if (!TOOL_LABELS[tool]) {
    state.tool = "select";
    renderAll();
    return;
  }
  state.tool = tool;
  if (!isLineDrawingTool(tool)) {
    ui.pendingPath = [];
  }
  clearSnapGuides();
  renderAll();
}

function setView(view) {
  if (!(view in FIELD_PRESETS)) {
    return;
  }
  state.view = view;
  state.panX = 0;
  state.panY = 0;
  commitProject();
}

function setZoom(nextZoom) {
  const normalized = clamp(round(nextZoom, 1), 1, 3);
  if (Math.abs(normalized - state.zoom) < 0.001) {
    renderToolbarState();
    return;
  }
  state.zoom = normalized;
  const panBounds = getPanBounds(currentPreset(), normalized);
  if (normalized <= 1) {
    state.panX = 0;
    state.panY = 0;
  } else {
    state.panX = clamp(state.panX, -panBounds.maxX, panBounds.maxX);
    state.panY = clamp(state.panY, -panBounds.maxY, panBounds.maxY);
  }
  renderBoard();
  renderToolbarState();
}

function stepZoom(step) {
  setZoom(state.zoom + step);
}

function setPan(nextPanX, nextPanY) {
  const panBounds = getPanBounds();
  state.panX = clamp(round(nextPanX), -panBounds.maxX, panBounds.maxX);
  state.panY = clamp(round(nextPanY), -panBounds.maxY, panBounds.maxY);
  renderBoard();
  renderToolbarState();
}

function nudgePan(direction) {
  if (state.zoom <= 1) {
    renderToolbarState();
    return;
  }
  const visibleBox = getBoardViewBox();
  const stepX = visibleBox.width * 0.14;
  const stepY = visibleBox.height * 0.14;

  if (direction === "up") {
    setPan(state.panX, state.panY - stepY);
    return;
  }
  if (direction === "down") {
    setPan(state.panX, state.panY + stepY);
    return;
  }
  if (direction === "left") {
    setPan(state.panX - stepX, state.panY);
    return;
  }
  if (direction === "right") {
    setPan(state.panX + stepX, state.panY);
    return;
  }
  setPan(0, 0);
}

function addObjectToCurrentFrame(object) {
  getCurrentFrame().objects.push(object);
  state.selectedId = object.id;
}

function clearSnapGuides() {
  ui.snapGuides = [];
}

function snapTargets(skipId) {
  const frame = getCurrentFrame();
  const crossTargets = [HASH_CROSS[state.playMeta.hash] ?? HASH_CROSS.middle, 50];
  const lengthTargets = driveMarkers(state.playMeta).map((marker) => marker.points[0].length);

  frame.objects.forEach((object) => {
    if (object.id === skipId || !isObjectVisible(object)) {
      return;
    }
    if (["player", "ball", "text", "zone"].includes(object.kind)) {
      crossTargets.push(object.cross);
      lengthTargets.push(object.length);
    }
  });

  return { crossTargets, lengthTargets };
}

function snapValue(value, targets, threshold = 1.2) {
  let best = null;
  for (const target of targets) {
    const distance = Math.abs(target - value);
    if (distance <= threshold && (!best || distance < best.distance)) {
      best = { value: target, distance };
    }
  }
  return best;
}

function guidesForSnap(cross, length) {
  const guides = [];
  if (typeof cross === "number") {
    const start = mapPoint(cross, 0);
    const end = mapPoint(cross, 100);
    guides.push({ axis: "cross", x1: start.x, y1: start.y, x2: end.x, y2: end.y });
  }
  if (typeof length === "number") {
    const start = mapPoint(0, length);
    const end = mapPoint(100, length);
    guides.push({ axis: "length", x1: start.x, y1: start.y, x2: end.x, y2: end.y });
  }
  return guides;
}

function applySnap(point, skipId) {
  if (!state.viewOptions.snap) {
    clearSnapGuides();
    return point;
  }

  const { crossTargets, lengthTargets } = snapTargets(skipId);
  const snappedCross = snapValue(point.cross, crossTargets);
  const snappedLength = snapValue(point.length, lengthTargets);
  ui.snapGuides = guidesForSnap(snappedCross?.value, snappedLength?.value);
  return {
    cross: snappedCross ? snappedCross.value : point.cross,
    length: snappedLength ? snappedLength.value : point.length,
  };
}

function placeBallAt(point) {
  const frame = getCurrentFrame();
  const snapped = applySnap(point);
  const existingBall = frame.objects.find((object) => object.kind === "ball");
  if (existingBall) {
    updateObject(existingBall.id, (object) => ({
      ...object,
      cross: snapped.cross,
      length: snapped.length,
    }));
    state.selectedId = existingBall.id;
  } else {
    addObjectToCurrentFrame(createBall(snapped.cross, snapped.length));
  }
}

function duplicateSelection() {
  const selected = findObject(state.selectedId);
  if (!selected || isObjectLocked(selected)) {
    return;
  }

  const copy = clone(selected);
  copy.id = uid();
  if (copy.kind === "path") {
    copy.points = copy.points.map((point) => ({
      cross: clamp(round(point.cross + 2.4), 0, 100),
      length: clamp(round(point.length - 2.4), 0, 100),
    }));
  } else if (copy.kind === "zone") {
    copy.cross = clamp(round(copy.cross + 2.4), 0, 100 - copy.crossSize);
    copy.length = clamp(round(copy.length - 2.4), 0, 100 - copy.lengthSize);
  } else {
    copy.cross = clamp(round(copy.cross + 2.4), 0, 100);
    copy.length = clamp(round(copy.length - 2.4), 0, 100);
  }
  addObjectToCurrentFrame(copy);
  commitProject();
}

function nudgeSelection(deltaCross, deltaLength) {
  const selected = findObject(state.selectedId);
  if (!selected || isObjectLocked(selected)) {
    return;
  }
  updateObject(selected.id, (object) => applyDrag(object, deltaCross, deltaLength));
  commitProject();
}

function insertTweenFrame() {
  const current = getCurrentFrame();
  const next = getFrameByIndex(state.currentFrameIndex + 1);
  if (!current || !next) {
    window.alert("중간 프레임을 만들려면 현재 프레임 뒤에 다음 프레임이 있어야 합니다.");
    return;
  }

  const ids = [
    ...current.objects.map((object) => object.id),
    ...next.objects.map((object) => object.id).filter((id) => !current.objects.some((item) => item.id === id)),
  ];
  const fromMap = new Map(current.objects.map((object) => [object.id, object]));
  const toMap = new Map(next.objects.map((object) => [object.id, object]));
  const tween = {
    id: uid(),
    name: `${current.name || "현재"} → ${next.name || "다음"} · 중간`,
    objects: ids
      .map((id) => interpolateObject(fromMap.get(id), toMap.get(id), 0.5))
      .filter(Boolean),
  };
  state.frames.splice(state.currentFrameIndex + 1, 0, ensureSingleBall(tween));
  state.currentFrameIndex += 1;
  commitProject();
}

function handleBoardPointerDown(event) {
  if (ui.playing) {
    return;
  }

  const target = event.target.closest("[data-object-id]");
  const objectId = target?.dataset.objectId;
  const isFieldSurface = Boolean(event.target.closest("[data-field-surface]"));
  const fieldPoint = screenToField(event);
  if (fieldPoint) {
    ui.pointerField = fieldPoint;
  }

  if (state.tool === "select") {
    if (objectId && fieldPoint) {
      state.selectedId = objectId;
      const object = findObject(objectId);
      if (!object) {
        renderAll();
        return;
      }
      if (isObjectLocked(object)) {
        renderAll();
        return;
      }

      ui.drag = {
        id: object.id,
        kind: object.kind,
        startedAt: fieldPoint,
        snapshot: clone(object),
        moved: false,
      };
      renderAll();
      return;
    }

    if (isFieldSurface && canDragFieldViewport()) {
      const visibleBox = getBoardViewBox();
      ui.panDrag = {
        pointerId: event.pointerId,
        startClientX: event.clientX,
        startClientY: event.clientY,
        startPanX: state.panX,
        startPanY: state.panY,
        viewWidth: visibleBox.width,
        viewHeight: visibleBox.height,
        moved: false,
      };
      syncBoardInteractionState();
      if (typeof refs.board.setPointerCapture === "function") {
        try {
          refs.board.setPointerCapture(event.pointerId);
        } catch (error) {
          console.debug("pointer capture skipped", error);
        }
      }
      return;
    }

    state.selectedId = null;
    renderAll();
    return;
  }

  if (!fieldPoint) {
    return;
  }

  if (state.tool === "offense" || state.tool === "defense") {
    if (isLayerLocked(state.tool)) {
      return;
    }
    if (isAddLimitReached(state.tool)) {
      renderAll();
      return;
    }
    const snapped = applySnap(fieldPoint);
    addObjectToCurrentFrame(createPlayer(state.tool, snapped.cross, snapped.length));
    clearSnapGuides();
    commitProject();
    return;
  }

  if (state.tool === "neutral") {
    if (isLayerLocked("neutral")) {
      return;
    }
    const snapped = applySnap(fieldPoint);
    addObjectToCurrentFrame(createPlayer("neutral", snapped.cross, snapped.length));
    clearSnapGuides();
    commitProject();
    return;
  }

  if (state.tool === "ball") {
    if (isLayerLocked("ball")) {
      return;
    }
    placeBallAt(fieldPoint);
    clearSnapGuides();
    commitProject();
    return;
  }

  if (state.tool === "text") {
    if (isLayerLocked("text")) {
      return;
    }
    const value = window.prompt("필드에 배치할 텍스트를 입력하세요.", "Motion");
    if (!value) {
      return;
    }
    const snapped = applySnap(fieldPoint);
    addObjectToCurrentFrame(createText(snapped.cross, snapped.length, value));
    clearSnapGuides();
    commitProject();
    return;
  }

  if (state.tool === "zone" || state.tool === "coverage") {
    if (isLayerLocked("zone")) {
      return;
    }
    const snapped = applySnap(fieldPoint);
    ui.zoneDraft = {
      start: snapped,
      current: snapped,
      overrides: zoneStyleForTool(state.tool),
    };
    renderBoard();
    renderToolbarState();
    return;
  }

  if (isLineDrawingTool(state.tool)) {
    if (isLayerLocked("path")) {
      return;
    }
    ui.pendingPath.push(applySnap(fieldPoint));
    renderBoard();
    renderToolbarState();
  }
}

function applyDrag(snapshot, deltaCross, deltaLength) {
  if (snapshot.kind === "player" || snapshot.kind === "text" || snapshot.kind === "ball") {
    return {
      ...snapshot,
      ...applySnap({
        cross: clamp(snapshot.cross + deltaCross, 0, 100),
        length: clamp(snapshot.length + deltaLength, 0, 100),
      }, snapshot.id),
    };
  }

  if (snapshot.kind === "zone") {
    const snapped = applySnap({
      cross: clamp(snapshot.cross + deltaCross, 0, 100 - snapshot.crossSize),
      length: clamp(snapshot.length + deltaLength, 0, 100 - snapshot.lengthSize),
    }, snapshot.id);
    return {
      ...snapshot,
      cross: snapped.cross,
      length: snapped.length,
    };
  }

  clearSnapGuides();
  if (snapshot.kind === "path") {
    const points = snapshot.points.map((point) => ({
      cross: clamp(point.cross + deltaCross, 0, 100),
      length: clamp(point.length + deltaLength, 0, 100),
    }));
    return { ...snapshot, points };
  }

  return snapshot;
}

function handlePointerMove(event) {
  const fieldPoint = screenToField(event);
  if (fieldPoint) {
    ui.pointerField = state.tool === "select" ? fieldPoint : applySnap(fieldPoint);
  }

  if (ui.panDrag) {
    const boardRect = refs.board.getBoundingClientRect();
    if (boardRect.width > 0 && boardRect.height > 0) {
      const deltaX = event.clientX - ui.panDrag.startClientX;
      const deltaY = event.clientY - ui.panDrag.startClientY;
      if (Math.hypot(deltaX, deltaY) > 4) {
        ui.panDrag.moved = true;
      }
      if (!ui.panDrag.moved) {
        return;
      }
      const panDeltaX = (deltaX / boardRect.width) * ui.panDrag.viewWidth;
      const panDeltaY = (deltaY / boardRect.height) * ui.panDrag.viewHeight;
      setPan(ui.panDrag.startPanX - panDeltaX, ui.panDrag.startPanY - panDeltaY);
    }
    return;
  }

  if (ui.drag && fieldPoint) {
    const deltaCross = fieldPoint.cross - ui.drag.startedAt.cross;
    const deltaLength = fieldPoint.length - ui.drag.startedAt.length;
    ui.drag.moved = true;
    updateObject(ui.drag.id, () => applyDrag(ui.drag.snapshot, deltaCross, deltaLength));
    renderBoard();
    renderInspector();
    return;
  }

  if (ui.zoneDraft && fieldPoint) {
    ui.zoneDraft.current = applySnap(fieldPoint);
    renderBoard();
    return;
  }

  if (isLineDrawingTool(state.tool) && ui.pendingPath.length) {
    renderBoard();
  }
}

function handlePointerUp(event) {
  if (ui.panDrag) {
    const shouldClearSelection = !ui.panDrag.moved;
    const pointerId = ui.panDrag.pointerId;
    ui.panDrag = null;
    if (
      typeof refs.board.releasePointerCapture === "function" &&
      typeof pointerId === "number"
    ) {
      try {
        if (!refs.board.hasPointerCapture || refs.board.hasPointerCapture(pointerId)) {
          refs.board.releasePointerCapture(pointerId);
        }
      } catch (error) {
        console.debug("pointer release skipped", error);
      }
    }
    syncBoardInteractionState();
    if (shouldClearSelection) {
      state.selectedId = null;
      renderAll();
    } else {
      clearSnapGuides();
      renderToolbarState();
    }
    return;
  }

  if (ui.drag) {
    const moved = ui.drag.moved;
    ui.drag = null;
    clearSnapGuides();
    if (moved) {
      commitProject();
    } else {
      renderAll();
    }
  }

  if (ui.zoneDraft) {
    const cross = Math.min(ui.zoneDraft.start.cross, ui.zoneDraft.current.cross);
    const length = Math.min(ui.zoneDraft.start.length, ui.zoneDraft.current.length);
    const crossSize = Math.abs(ui.zoneDraft.start.cross - ui.zoneDraft.current.cross);
    const lengthSize = Math.abs(ui.zoneDraft.start.length - ui.zoneDraft.current.length);
    const overrides = ui.zoneDraft.overrides || {};
    ui.zoneDraft = null;
    clearSnapGuides();
    if (crossSize > 1 && lengthSize > 1) {
      addObjectToCurrentFrame(createZone(cross, length, crossSize, lengthSize, overrides));
      commitProject();
    } else {
      renderAll();
    }
  }
}

function finishPendingPath() {
  if (isLayerLocked("path")) {
    return;
  }
  if (ui.pendingPath.length < 2) {
    return;
  }
  const selected = findObject(state.selectedId);
  addObjectToCurrentFrame(
    createPath(clone(ui.pendingPath), pathStyleForTool(state.tool, selected)),
  );
  ui.pendingPath = [];
  clearSnapGuides();
  commitProject();
}

function cancelPendingPath() {
  ui.pendingPath = [];
  clearSnapGuides();
  renderAll();
}

function updateSelectedField(field, value) {
  const selected = findObject(state.selectedId);
  if (!selected || isObjectLocked(selected)) {
    return;
  }
  updateObject(selected.id, (object) => {
    const next = { ...object, [field]: value };
    if (field === "team" && object.kind === "player") {
      next.color = TEAM_COLORS[value];
    }
    if (field === "lineStyle" && object.kind === "path") {
      next.lineStyle = ["solid", "dashed", "motion"].includes(value) ? value : "solid";
      next.dashed = next.lineStyle !== "solid";
    }
    if (field === "cross") {
      next.cross = clamp(Number(value), 0, 100);
    }
    if (field === "length") {
      next.length = clamp(Number(value), 0, 100);
    }
    if (field === "scale" && object.kind === "ball") {
      next.scale = clamp(Number(value), 0.6, 1.6);
    }
    if (field === "crossSize") {
      next.crossSize = clamp(Number(value), 1, 100);
      next.cross = clamp(next.cross, 0, 100 - next.crossSize);
    }
    if (field === "lengthSize") {
      next.lengthSize = clamp(Number(value), 1, 100);
      next.length = clamp(next.length, 0, 100 - next.lengthSize);
    }
    return next;
  });
}

function parseInputValue(input) {
  const type = input.dataset.type || input.type;
  if (type === "number" || input.type === "range" || input.type === "number") {
    return Number(input.value);
  }
  if (type === "boolean") {
    return input.value === "true";
  }
  return input.value;
}

function updatePlayMeta(field, value) {
  const next = { ...state.playMeta, [field]: value };
  if (field === "down") {
    next.down = clamp(Number(value), 1, 4);
  }
  if (field === "distance") {
    next.distance = clamp(Number(value), 1, 40);
  }
  if (field === "ballOn") {
    next.ballOn = clamp(Number(value), 1, 99);
  }
  if (field === "hash") {
    next.hash = ["left", "middle", "right"].includes(value) ? value : "middle";
  }
  state.playMeta = next;
}

function syncPlaySettingsPreview(field, input) {
  const scope = input.closest(".field-inline");
  if (!scope) {
    return;
  }
  const display = scope.querySelector("[data-play-display]");
  if (!display) {
    return;
  }
  if (field === "distance") {
    display.textContent = `${state.playMeta.distance} yd`;
  }
  if (field === "ballOn") {
    display.textContent = ballOnLabel(state.playMeta.ballOn);
  }
}

function handlePlaySettingsInput(event) {
  const input = event.target.closest("[data-play-field]");
  if (!input || input.type !== "range") {
    return;
  }
  updatePlayMeta(input.dataset.playField, parseInputValue(input));
  syncPlaySettingsPreview(input.dataset.playField, input);
  renderBoard();
  renderProjectSummary();
}

function handlePlaySettingsChange(event) {
  const input = event.target.closest("[data-play-field]");
  if (!input) {
    return;
  }
  updatePlayMeta(input.dataset.playField, parseInputValue(input));
  commitProject();
}

function handleLayerPanelChange(event) {
  const input = event.target.closest("[data-layer-key]");
  if (!input) {
    return;
  }
  const layerKey = input.dataset.layerKey;
  const field = input.dataset.layerField;
  state.layers = {
    ...state.layers,
    [layerKey]: {
      ...state.layers[layerKey],
      [field]: input.checked,
    },
  };
  if (field === "visible" && !input.checked) {
    const selected = findObject(state.selectedId);
    if (selected && objectLayerKey(selected) === layerKey) {
      state.selectedId = null;
    }
  }
  commitProject();
}

function handleInspectorInput(event) {
  const input = event.target.closest("[data-field]");
  if (!input || !state.selectedId) {
    return;
  }
  updateSelectedField(input.dataset.field, parseInputValue(input));
  renderBoard();
  renderProjectSummary();
}

function handleInspectorChange(event) {
  const input = event.target.closest("[data-field]");
  if (!input || !state.selectedId) {
    return;
  }
  updateSelectedField(input.dataset.field, parseInputValue(input));
  commitProject();
}

function addFrame() {
  const current = getCurrentFrame();
  const copy = clone(current);
  copy.id = uid();
  copy.name = `${current.name || `프레임 ${state.currentFrameIndex + 1}`} 복제`;
  state.frames.splice(state.currentFrameIndex + 1, 0, copy);
  state.currentFrameIndex += 1;
  commitProject();
}

function removeFrame() {
  if (state.frames.length === 1) {
    window.alert("최소 1개의 프레임은 유지해야 합니다.");
    return;
  }
  state.frames.splice(state.currentFrameIndex, 1);
  state.currentFrameIndex = clamp(state.currentFrameIndex, 0, state.frames.length - 1);
  state.selectedId = null;
  commitProject();
}

function renameFrame() {
  const current = getCurrentFrame();
  const nextName = window.prompt("프레임 이름을 입력하세요.", current.name || "");
  if (!nextName) {
    return;
  }
  current.name = nextName;
  commitProject();
}

function selectFrame(index) {
  state.currentFrameIndex = clamp(index, 0, state.frames.length - 1);
  stopPlayback(false);
  renderAll();
}

function historyStep(direction) {
  const nextIndex = ui.historyIndex + direction;
  if (nextIndex < 0 || nextIndex >= ui.history.length) {
    return;
  }
  ui.historyIndex = nextIndex;
  applyProjectData(ui.history[nextIndex].snapshot);
  renderAll();
}

function startPlayback() {
  if (state.frames.length < 2) {
    window.alert("애니메이션을 보려면 프레임을 2개 이상 만들어주세요.");
    return;
  }
  ui.playing = true;
  ui.playbackBaseOffset = 0;
  ui.playbackStartFrame =
    state.currentFrameIndex >= state.frames.length - 1 ? 0 : state.currentFrameIndex;
  ui.playbackStartedAt = performance.now();
  tickPlayback(ui.playbackStartedAt);
  renderToolbarState();
}

function stopPlayback(keepNearestFrame = true) {
  if (ui.rafId) {
    cancelAnimationFrame(ui.rafId);
  }
  if (keepNearestFrame && ui.preview) {
    state.currentFrameIndex = ui.preview.t > 0.5 ? ui.preview.to : ui.preview.from;
  }
  ui.playing = false;
  ui.preview = null;
  ui.rafId = 0;
}

function tickPlayback(now) {
  const segmentCount = state.frames.length - 1 - ui.playbackStartFrame;
  const totalDuration = segmentCount * state.frameDuration;
  const elapsed = now - ui.playbackStartedAt + ui.playbackBaseOffset;

  if (elapsed >= totalDuration) {
    stopPlayback(true);
    renderAll();
    return;
  }

  const segmentIndex = Math.floor(elapsed / state.frameDuration);
  const localElapsed = elapsed - segmentIndex * state.frameDuration;
  ui.preview = {
    from: ui.playbackStartFrame + segmentIndex,
    to: ui.playbackStartFrame + segmentIndex + 1,
    t: localElapsed / state.frameDuration,
  };

  renderBoard();
  renderToolbarState();
  ui.rafId = requestAnimationFrame(tickPlayback);
}

function togglePlayback() {
  if (ui.playing) {
    stopPlayback(true);
    renderAll();
    return;
  }
  startPlayback();
}

function resetPlayback() {
  stopPlayback(false);
  state.currentFrameIndex = 0;
  renderAll();
}

function deleteSelection() {
  if (!state.selectedId) {
    return;
  }
  const selected = findObject(state.selectedId);
  if (!selected || isObjectLocked(selected)) {
    return;
  }
  deleteObject(state.selectedId);
  commitProject();
}

function handleFrameStripClick(event) {
  const button = event.target.closest("[data-frame-index]");
  if (!button) {
    return;
  }
  selectFrame(Number(button.dataset.frameIndex));
}

function loadDemo() {
  applyProjectData(buildDemoProject());
  ui.history = [];
  ui.historyIndex = -1;
  pushHistory();
  persistProject();
  renderAll();
}

function resetProjectToDefaultFormation() {
  const confirmed = window.confirm(
    "현재 작업 내용을 지우고 40야드 기준 11 personnel 오펜스와 4-3 디펜스로 초기화할까요?",
  );
  if (!confirmed) {
    return;
  }
  applyProjectData(buildDefaultFormationProject());
  ui.history = [];
  ui.historyIndex = -1;
  pushHistory();
  persistProject();
  renderAll();
}

function downloadFile(filename, blob) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

function svgSource() {
  const cloneSvg = refs.board.cloneNode(true);
  const preset = currentPreset();
  cloneSvg.querySelectorAll(".field-surface, .guide-line, .guide-line--secondary").forEach((node) => node.remove());
  cloneSvg.setAttribute("xmlns", SVG_NS);
  cloneSvg.setAttribute("viewBox", `0 0 ${preset.viewBox.width} ${preset.viewBox.height}`);
  cloneSvg.setAttribute("width", preset.viewBox.width);
  cloneSvg.setAttribute("height", preset.viewBox.height);
  cloneSvg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  return new XMLSerializer().serializeToString(cloneSvg);
}

function exportJson() {
  const blob = new Blob([JSON.stringify(getProjectData(), null, 2)], {
    type: "application/json",
  });
  downloadFile(`${slugifyFilename(state.playMeta.title)}.json`, blob);
}

function exportSvg() {
  const blob = new Blob([svgSource()], {
    type: "image/svg+xml;charset=utf-8",
  });
  downloadFile(`${slugifyFilename(state.playMeta.title)}.svg`, blob);
}

async function exportPng() {
  const src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgSource())}`;
  const image = new Image();
  const preset = currentPreset();
  const scale = 2;

  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = reject;
    image.src = src;
  });

  const canvas = document.createElement("canvas");
  canvas.width = preset.viewBox.width * scale;
  canvas.height = preset.viewBox.height * scale;
  const context = canvas.getContext("2d");
  context.scale(scale, scale);
  context.drawImage(image, 0, 0);

  canvas.toBlob((blob) => {
    if (!blob) {
      return;
    }
    downloadFile(`${slugifyFilename(state.playMeta.title)}.png`, blob);
  }, "image/png");
}

function importJson(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = JSON.parse(String(reader.result));
      if (!parsed || !Array.isArray(parsed.frames) || !parsed.frames.length) {
        throw new Error("잘못된 파일 형식");
      }
      applyProjectData(parsed);
      ui.history = [];
      ui.historyIndex = -1;
      pushHistory();
      persistProject();
      renderAll();
    } catch (error) {
      window.alert("JSON 파일을 읽지 못했습니다.");
    }
  };
  reader.readAsText(file);
}

function handleKeydown(event) {
  const targetTag = document.activeElement?.tagName;
  const isFormField = ["INPUT", "TEXTAREA", "SELECT"].includes(targetTag);

  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "d") {
    event.preventDefault();
    duplicateSelection();
    return;
  }

  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z") {
    event.preventDefault();
    historyStep(event.shiftKey ? 1 : -1);
    return;
  }

  if (isFormField) {
    return;
  }

  if (event.key === "Delete" || event.key === "Backspace") {
    deleteSelection();
    return;
  }

  if (event.key === "Enter" && isLineDrawingTool(state.tool)) {
    finishPendingPath();
    return;
  }

  if (event.key === "Escape") {
    cancelPendingPath();
    ui.zoneDraft = null;
    renderAll();
  }

  const key = event.key.toLowerCase();
  const toolHotkeys = {
    v: "select",
    o: "offense",
    d: "defense",
    n: "neutral",
    b: "ball",
    r: "path",
    m: "motion",
    g: "block",
    x: "rush",
    z: "zone",
    c: "coverage",
    t: "text",
  };
  if (toolHotkeys[key]) {
    event.preventDefault();
    setTool(toolHotkeys[key]);
    return;
  }

  if (key === "i") {
    event.preventDefault();
    insertTweenFrame();
    return;
  }

  if (!state.selectedId) {
    return;
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    nudgeSelection(0, -0.6);
    return;
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    nudgeSelection(0, 0.6);
    return;
  }
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    nudgeSelection(-0.6, 0);
    return;
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    nudgeSelection(0.6, 0);
  }
}

function bindEvents() {
  document.querySelectorAll("[data-tool]").forEach((button) => {
    button.addEventListener("click", () => setTool(button.dataset.tool));
  });

  document.querySelectorAll("[data-route-preset]").forEach((button) => {
    button.addEventListener("click", () => insertRoutePreset(button.dataset.routePreset));
  });

  refs.conceptPresetGrid.addEventListener("click", (event) => {
    const button = event.target.closest("[data-concept-preset]");
    if (!button) {
      return;
    }
    insertConceptPreset(button.dataset.conceptPreset);
  });

  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });

  refs.board.addEventListener("pointerdown", handleBoardPointerDown);
  window.addEventListener("pointermove", handlePointerMove);
  window.addEventListener("pointerup", handlePointerUp);
  window.addEventListener("pointercancel", handlePointerUp);
  window.addEventListener("keydown", handleKeydown);
  refs.frameStrip.addEventListener("click", handleFrameStripClick);
  refs.inspectorContent.addEventListener("input", handleInspectorInput);
  refs.inspectorContent.addEventListener("change", handleInspectorChange);
  refs.playSettingsPanel.addEventListener("input", handlePlaySettingsInput);
  refs.playSettingsPanel.addEventListener("change", handlePlaySettingsChange);
  refs.layerPanel.addEventListener("change", handleLayerPanelChange);

  refs.frameDurationRange.addEventListener("input", () => {
    state.frameDuration = Number(refs.frameDurationRange.value);
    renderToolbarState();
  });

  refs.frameDurationRange.addEventListener("change", () => {
    state.frameDuration = Number(refs.frameDurationRange.value);
    commitProject();
  });

  refs.zoomRange.addEventListener("input", () => {
    setZoom(Number(refs.zoomRange.value) / 100);
  });
  refs.zoomOutBtn.addEventListener("click", () => stepZoom(-0.1));
  refs.zoomInBtn.addEventListener("click", () => stepZoom(0.1));
  refs.zoomResetBtn.addEventListener("click", () => setZoom(1));
  refs.panUpBtn.addEventListener("click", () => nudgePan("up"));
  refs.panLeftBtn.addEventListener("click", () => nudgePan("left"));
  refs.panRightBtn.addEventListener("click", () => nudgePan("right"));
  refs.panDownBtn.addEventListener("click", () => nudgePan("down"));
  refs.panCenterBtn.addEventListener("click", () => setPan(0, 0));
  refs.snapToggleBtn.addEventListener("click", () => {
    state.viewOptions = { ...state.viewOptions, snap: !state.viewOptions.snap };
    commitProject();
  });
  refs.onionSkinBtn.addEventListener("click", () => {
    state.viewOptions = {
      ...state.viewOptions,
      onionSkin: !state.viewOptions.onionSkin,
    };
    commitProject();
  });
  refs.routeColorInput.addEventListener("input", () => {
    state.routeColor = refs.routeColorInput.value;
    persistProject();
    renderBoard();
    renderToolbarState();
  });
  refs.routeLineStyleSelect.addEventListener("change", () => {
    if (refs.routeLineStyleSelect.value === "motion") {
      state.routeLineStyle = "motion";
    } else {
      state.routeLineStyle = refs.routeLineStyleSelect.value;
    }
    persistProject();
    renderBoard();
    renderToolbarState();
  });

  document.getElementById("undoBtn").addEventListener("click", () => historyStep(-1));
  document.getElementById("redoBtn").addEventListener("click", () => historyStep(1));
  document.getElementById("playBtn").addEventListener("click", togglePlayback);
  document.getElementById("resetPlaybackBtn").addEventListener("click", resetPlayback);
  document.getElementById("deleteSelectionBtn").addEventListener("click", deleteSelection);
  document.getElementById("finishPathBtn").addEventListener("click", finishPendingPath);
  document.getElementById("cancelPathBtn").addEventListener("click", cancelPendingPath);
  document.getElementById("addFrameBtn").addEventListener("click", addFrame);
  refs.tweenFrameBtn.addEventListener("click", insertTweenFrame);
  document.getElementById("removeFrameBtn").addEventListener("click", removeFrame);
  document.getElementById("renameFrameBtn").addEventListener("click", renameFrame);
  document
    .getElementById("resetProjectBtn")
    .addEventListener("click", resetProjectToDefaultFormation);
  document.getElementById("loadDemoBtn").addEventListener("click", loadDemo);
  document.getElementById("exportJsonBtn").addEventListener("click", exportJson);
  document.getElementById("exportSvgBtn").addEventListener("click", exportSvg);
  document.getElementById("exportPngBtn").addEventListener("click", () => {
    exportPng().catch(() => window.alert("PNG 내보내기에 실패했습니다."));
  });
  document.getElementById("importJsonBtn").addEventListener("click", () =>
    refs.importInput.click(),
  );
  refs.importInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    if (file) {
      importJson(file);
    }
    refs.importInput.value = "";
  });
}

function initialize() {
  const saved = loadProjectFromStorage();
  applyProjectData(saved || buildDemoProject());
  pushHistory();
  if (saved) {
    ui.lastSavedAt = new Date();
  } else {
    persistProject();
  }
  renderConceptPresetLibrary();
  bindEvents();
  renderAll();
}

initialize();
