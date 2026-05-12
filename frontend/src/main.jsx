import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const FACES = ["top", "bottom", "front", "back", "left", "right", "custom"];

const OPERATIONS = [
  ["cut",        "Cut"],
  ["screw_hole", "Screw hole"],
  ["connector",  "Connector cutout"],
  ["boss",       "Boss / standoff"],
  ["add_solid",  "Add solid"],
];

// Shapes grouped by operation context
const SHAPES_CUT = [
  ["circle",       "Circle"],
  ["rect",         "Rectangle"],
  ["rounded_rect", "Rounded rectangle"],
  ["slot",         "Slot"],
];
const SHAPES_HOLE = [
  ["circle", "Circle"],
  ["slot",   "Slot"],
];
const SHAPES_CONNECTOR = [
  ["usb_c",        "USB-C"],
  ["usb_a",        "USB-A"],
  ["hdmi",         "HDMI"],
  ["dc_jack",      "DC jack"],
  ["rect",         "Rectangle"],
  ["rounded_rect", "Rounded rectangle"],
];
const SHAPES_SOLID = [
  ["circle", "Cylinder"],
  ["rect",   "Box"],
];

const CONNECTOR_DIMS = {
  usb_c:   { width: 9.0,  height: 3.4, cornerRadius: 1.7 },
  usb_a:   { width: 14.0, height: 6.5, cornerRadius: 0.5 },
  hdmi:    { width: 14.0, height: 6.0, cornerRadius: 0.6 },
  dc_jack: { diameter: 8.0 },
};

const DEPTH_MODES = [
  ["through",    "Through All"],
  ["blind",      "Blind"],
  ["up_to_next", "Up to Next Surface"],
  ["custom",     "Custom depth (mm)"],
];

const PATTERNS = [
  ["single",   "Single"],
  ["linear",   "Linear pattern"],
  ["grid",     "Rectangular grid"],
  ["circular", "Circular pattern"],
];

const SCREW_SIZES = ["M1", "M1.2", "M1.6", "M2", "M2.5", "M3", "M4", "M5", "M6", "M8", "M10"];

const OP_ICONS = {
  cut:        "⊟",
  screw_hole: "◎",
  connector:  "▣",
  boss:       "⬡",
  add_solid:  "⬛",
  hole:       "○",
};

// ISO M-series specs: clear_n/c/l=clearance normal/close/loose, cbore_d/h=counterbore, csk_d/a=countersink, tap_d=tap drill
const SCREW_SPECS = {
  M1:   { clear_n:1.2, clear_c:1.1, clear_l:1.3, cbore_d:2.5,  cbore_h:1.0,  csk_d:2.0,  csk_a:90, tap_d:0.75 },
  M1_2: { clear_n:1.4, clear_c:1.3, clear_l:1.6, cbore_d:3.0,  cbore_h:1.2,  csk_d:2.4,  csk_a:90, tap_d:0.95 },
  M1_6: { clear_n:1.8, clear_c:1.7, clear_l:2.0, cbore_d:3.5,  cbore_h:1.6,  csk_d:3.0,  csk_a:90, tap_d:1.25 },
  M2:   { clear_n:2.4, clear_c:2.2, clear_l:2.6, cbore_d:4.4,  cbore_h:2.0,  csk_d:3.8,  csk_a:90, tap_d:1.6  },
  M2_5: { clear_n:2.9, clear_c:2.7, clear_l:3.1, cbore_d:5.4,  cbore_h:2.5,  csk_d:4.7,  csk_a:90, tap_d:2.05 },
  M3:   { clear_n:3.4, clear_c:3.2, clear_l:3.6, cbore_d:6.0,  cbore_h:3.0,  csk_d:5.5,  csk_a:90, tap_d:2.5  },
  M4:   { clear_n:4.5, clear_c:4.3, clear_l:4.8, cbore_d:8.0,  cbore_h:4.0,  csk_d:7.4,  csk_a:90, tap_d:3.3  },
  M5:   { clear_n:5.5, clear_c:5.3, clear_l:5.8, cbore_d:10.0, cbore_h:5.0,  csk_d:9.2,  csk_a:90, tap_d:4.2  },
  M6:   { clear_n:6.6, clear_c:6.4, clear_l:7.0, cbore_d:11.0, cbore_h:6.0,  csk_d:11.0, csk_a:90, tap_d:5.0  },
  M8:   { clear_n:9.0, clear_c:8.4, clear_l:9.5, cbore_d:14.5, cbore_h:8.0,  csk_d:14.5, csk_a:90, tap_d:6.75 },
  M10:  { clear_n:11.0,clear_c:10.5,clear_l:11.5,cbore_d:18.0, cbore_h:10.0, csk_d:18.0, csk_a:90, tap_d:8.5  },
};

// Map dropdown value (e.g. "M1.2") to SCREW_SPECS key
function specKey(size) { return size.replace(/\./g, "_"); }

const HOLE_TYPES = [
  { id: "clearance",   label: "Simple",  desc: "Clearance hole" },
  { id: "counterbore", label: "Cbore",   desc: "Counterbore" },
  { id: "countersink", label: "Csk",     desc: "Countersink (angled)" },
  { id: "tapped",      label: "Tapped",  desc: "Tapped hole" },
];

const FIT_OPTIONS = [
  ["normal", "Normal"],
  ["close",  "Close"],
  ["loose",  "Loose"],
];

function getScrewDims(holeType, screwSize, fit = "normal") {
  const spec = SCREW_SPECS[specKey(screwSize)];
  if (!spec) return { diameter: 3 };
  const clearD = { normal: spec.clear_n, close: spec.clear_c, loose: spec.clear_l }[fit] ?? spec.clear_n;
  if (holeType === "clearance")   return { diameter: clearD };
  if (holeType === "counterbore") return { diameter: clearD, counterboreDiameter: spec.cbore_d, counterboreDepth: spec.cbore_h };
  if (holeType === "countersink") return { diameter: clearD, countersinkDiameter: spec.csk_d, countersinkAngle: spec.csk_a };
  if (holeType === "tapped")      return { diameter: spec.tap_d };
  return { diameter: clearD };
}

const starterBody = {
  name: "Plane Operation Model",
  length: 100,
  width: 60,
  height: 35,
  wall: 2,
  fillet_radius: 1.5,
  solid: false,
};

function createBlock(index = 0) {
  return {
    id: `op_${Date.now()}_${index}`,
    label: `Plane Operation ${index + 1}`,
    enabled: true,
    plane: index === 1 ? "front" : "top",
    customPlane: { originX: 0, originY: 0, originZ: 20, normalX: 0, normalY: 0, normalZ: 1, rotation: 0 },
    operation: index === 1 ? "connector" : "screw_hole",
    shape: index === 1 ? "usb_c" : "circle",
    x: 0, y: 0, z: 0, offset: 0, rotation: 0,
    depthMode: index === 1 ? "blind" : "through",
    depth: index === 1 ? 4 : 10,
    diameter: 3,
    width: index === 1 ? 9 : 16,
    height: index === 1 ? 3.4 : 8,
    cornerRadius: index === 1 ? 1.7 : 1,
    slotLength: 20, slotWidth: 5,
    screwSize: "M3",
    holeType: "clearance",
    fit: "normal",
    showCustom: false,
    counterboreDiameter: 6, counterboreDepth: 2,
    countersinkDiameter: 0, countersinkAngle: 90,
    bossOuterDiameter: 8, bossHeight: 6,
    patternType: index === 0 ? "grid" : "single",
    linearCount: 2, linearSpacing: 12,
    directionX: 1, directionY: 0, directionZ: 0,
    rows: 2, columns: 2, rowSpacing: 40, columnSpacing: 70,
    circularCount: 6, centerX: 0, centerY: 0, circularRadius: 20, angleStep: 60,
    showAdvanced: false,
  };
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function updateArrayItem(items, id, updater) {
  return items.map((item) => (item.id === id ? updater({ ...item }) : item));
}

function planePlacement(block) {
  const base = { u: toNumber(block.x), v: toNumber(block.y) };
  if (block.plane === "custom") {
    return {
      ...base,
      plane: {
        origin: { x: toNumber(block.customPlane.originX), y: toNumber(block.customPlane.originY), z: toNumber(block.customPlane.originZ) },
        normal: { x: toNumber(block.customPlane.normalX), y: toNumber(block.customPlane.normalY), z: toNumber(block.customPlane.normalZ, 1) },
        x_dir: { x: 1, y: 0, z: 0 },
        rotation: toNumber(block.customPlane.rotation),
      },
    };
  }
  return { ...base, face: block.plane };
}

function patternFromBlock(block) {
  if (block.patternType === "single") return undefined;
  if (block.patternType === "linear") {
    return {
      type: "linear",
      count: Math.max(1, toNumber(block.linearCount, 1)),
      spacing: Math.max(0.1, toNumber(block.linearSpacing, 1)),
      direction: { x: toNumber(block.directionX, 1), y: toNumber(block.directionY), z: toNumber(block.directionZ) },
    };
  }
  if (block.patternType === "grid") {
    return {
      type: "grid",
      rows: Math.max(1, toNumber(block.rows, 1)),
      columns: Math.max(1, toNumber(block.columns, 1)),
      row_spacing: Math.max(0.1, toNumber(block.rowSpacing, 1)),
      column_spacing: Math.max(0.1, toNumber(block.columnSpacing, 1)),
    };
  }
  return {
    type: "circular",
    count: Math.max(1, toNumber(block.circularCount, 1)),
    center: { x: toNumber(block.centerX), y: toNumber(block.centerY) },
    radius: Math.max(0, toNumber(block.circularRadius)),
    angle_step: toNumber(block.angleStep, 360 / Math.max(1, toNumber(block.circularCount, 1))),
  };
}

function depthFields(block) {
  if (block.depthMode === "through" || block.depthMode === "up_to_next") return { through: true };
  return { through: false, depth: Math.max(0.1, toNumber(block.depth, 1)) };
}

function shapeFields(block) {
  const shape = block.shape;
  if (shape === "circle" || shape === "dc_jack") return { diameter: Math.max(0.1, toNumber(block.diameter, 3)) };
  if (shape === "slot") return { slot_length: Math.max(0.1, toNumber(block.slotLength, 10)), diameter: Math.max(0.1, toNumber(block.slotWidth, 3)), radius: Math.max(0, toNumber(block.slotWidth, 3) / 2) };
  if (["usb_c", "usb_a", "hdmi"].includes(shape)) return { width: Math.max(0.1, toNumber(block.width, 9)), height: Math.max(0.1, toNumber(block.height, 3.4)), corner_radius: Math.max(0, toNumber(block.cornerRadius)) };
  return { width: Math.max(0.1, toNumber(block.width, 10)), height: Math.max(0.1, toNumber(block.height, 8)), corner_radius: Math.max(0, toNumber(block.cornerRadius)) };
}

function featureFromBlock(block) {
  const id = block.id.replace(/[^a-zA-Z0-9_]/g, "_");
  const placement = planePlacement(block);
  const pattern = patternFromBlock(block);
  const common = { id, target: "shell", placement, pattern };

  if (block.operation === "boss") {
    return {
      type: "boss", ...common,
      outer_diameter: Math.max(0.1, toNumber(block.bossOuterDiameter, 8)),
      inner_hole_diameter: Math.max(0.1, toNumber(block.diameter, 3)),
      height: Math.max(0.1, toNumber(block.bossHeight, 6)),
      counterbore_diameter: block.counterboreDiameter ? toNumber(block.counterboreDiameter) : undefined,
      counterbore_depth: block.counterboreDepth ? toNumber(block.counterboreDepth) : undefined,
    };
  }

  if (block.operation === "screw_hole") {
    const ht = block.holeType || "clearance";
    const dims = !block.showCustom ? getScrewDims(ht, block.screwSize, block.fit || "normal") : {};
    const dia = block.showCustom ? Math.max(0.1, toNumber(block.diameter, 3)) : (dims.diameter ?? 3);
    const cboreD = (ht === "counterbore")
      ? (block.showCustom ? toNumber(block.counterboreDiameter) : (dims.counterboreDiameter ?? 0))
      : undefined;
    const cboreH = (ht === "counterbore")
      ? (block.showCustom ? toNumber(block.counterboreDepth) : (dims.counterboreDepth ?? 0))
      : undefined;
    const cskD = (ht === "countersink")
      ? (block.showCustom ? toNumber(block.countersinkDiameter) : (dims.countersinkDiameter ?? 0))
      : undefined;
    const cskA = (ht === "countersink")
      ? (block.showCustom ? toNumber(block.countersinkAngle, 90) : (dims.countersinkAngle ?? 90))
      : undefined;
    return {
      type: "screw_hole",
      ...common,
      diameter: dia,
      ...depthFields(block),
      counterbore_diameter: cboreD,
      counterbore_depth: cboreH,
      countersink_diameter: cskD,
      countersink_angle: cskA,
      thread: block.screwSize || undefined,
    };
  }

  if (block.operation === "hole") {
    return {
      type: "hole",
      ...common,
      diameter: Math.max(0.1, toNumber(block.diameter, 3)),
      ...depthFields(block),
      counterbore_diameter: block.counterboreDiameter ? toNumber(block.counterboreDiameter) : undefined,
      counterbore_depth: block.counterboreDepth ? toNumber(block.counterboreDepth) : undefined,
      countersink_diameter: block.countersinkDiameter ? toNumber(block.countersinkDiameter) : undefined,
      countersink_angle: toNumber(block.countersinkAngle, 90),
    };
  }

  if (block.operation === "add_solid") {
    const position = { x: toNumber(block.x), y: toNumber(block.y), z: toNumber(block.z) };
    if (block.shape === "circle") return { type: "cylinder", id, target: "shell", operation: "union", position, diameter: Math.max(0.1, toNumber(block.diameter, 5)), height: Math.max(0.1, toNumber(block.depth, 8)) };
    return { type: "box", id, target: "shell", operation: "union", position, rotation: { x: 0, y: 0, z: toNumber(block.rotation) }, length: Math.max(0.1, toNumber(block.width, 12)), width: Math.max(0.1, toNumber(block.height, 8)), height: Math.max(0.1, toNumber(block.depth, 6)) };
  }

  const shape = block.operation === "connector" ? block.shape : block.shape;
  return { type: "cutout", ...common, shape, rotation: toNumber(block.rotation), ...depthFields(block), ...shapeFields(block) };
}

function buildProject(body, blocks) {
  const features = [
    body.solid
      ? { type: "box", id: "shell", length: "L", width: "W", height: "H", fillet_radius: Math.max(0, toNumber(body.fillet_radius, 0)) }
      : { type: "enclosure", id: "shell", length: "L", width: "W", height: "H", wall: "wall", fillet_radius: Math.max(0, toNumber(body.fillet_radius, 0)) },
    ...blocks.filter((b) => b.enabled).map(featureFromBlock),
  ];
  return {
    name: body.name || "Parametric CAD Model",
    parameters: [
      { name: "L",    value: Math.max(1, toNumber(body.length, 100)) },
      { name: "W",    value: Math.max(1, toNumber(body.width, 60)) },
      { name: "H",    value: Math.max(1, toNumber(body.height, 35)) },
      { name: "wall", value: Math.max(0.1, toNumber(body.wall, 2)) },
    ],
    features,
  };
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = filename; link.click();
  URL.revokeObjectURL(url);
}

// ── 3D Preview ────────────────────────────────────────────────────────────────

function placeModelAtCornerOrigin(model, controls, camera) {
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  // Corner at origin: move min point to (0,0,0)
  model.position.set(-box.min.x, -box.min.y, -box.min.z);
  // Target the center of the placed model
  const center = new THREE.Vector3(size.x / 2, size.y / 2, size.z / 2);
  controls.target.copy(center);
  // Fit camera: stand back far enough to see the whole model
  const maxDim = Math.max(size.x, size.y, size.z);
  const dist = maxDim * 2.2;
  camera.position.copy(center).add(new THREE.Vector3(dist * 0.7, dist * 0.5, dist * 0.9));
  controls.update();
}

function Preview({ previewUrl, previewKind, selectedPlane }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#080b12");

    const camera = new THREE.PerspectiveCamera(45, mount.clientWidth / mount.clientHeight, 0.1, 5000);
    camera.position.set(120, -150, 90);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    // Grid on the floor (y=0 plane)
    const grid = new THREE.GridHelper(500, 50, "#1f3b73", "#14213f");
    grid.position.set(0, 0, 0);
    scene.add(grid);
    scene.add(new THREE.AxesHelper(26));
    scene.add(new THREE.HemisphereLight("#ffffff", "#26354f", 2.6));
    const key = new THREE.DirectionalLight("#ffffff", 2);
    key.position.set(100, 80, 120);
    key.castShadow = true;
    scene.add(key);

    // Selected plane indicator (model exported Z-up from CadQuery, rotated -PI/2 around X so CadQuery Z → Three.js Y)
    if (selectedPlane && selectedPlane !== "custom") {
      const planeMesh = new THREE.Mesh(
        new THREE.PlaneGeometry(80, 50),
        new THREE.MeshBasicMaterial({ color: "#38bdf8", transparent: true, opacity: 0.15, side: THREE.DoubleSide })
      );
      if (selectedPlane === "top") {
        planeMesh.rotation.x = -Math.PI / 2;
        planeMesh.position.set(50, 37, 30);
      } else if (selectedPlane === "bottom") {
        planeMesh.rotation.x = -Math.PI / 2;
        planeMesh.position.set(50, 0, 30);
      } else if (selectedPlane === "front") {
        planeMesh.position.set(50, 18, 62);
      } else if (selectedPlane === "back") {
        planeMesh.rotation.y = Math.PI;
        planeMesh.position.set(50, 18, -2);
      } else if (selectedPlane === "left") {
        planeMesh.rotation.y = Math.PI / 2;
        planeMesh.position.set(-2, 18, 30);
      } else if (selectedPlane === "right") {
        planeMesh.rotation.y = -Math.PI / 2;
        planeMesh.position.set(102, 18, 30);
      }
      scene.add(planeMesh);
    }

    let model = null;
    if (previewUrl && previewKind === "stl") {
      new STLLoader().load(previewUrl, (geometry) => {
        const mesh = new THREE.Mesh(
          geometry,
          new THREE.MeshStandardMaterial({ color: "#3b82f6", roughness: 0.55, metalness: 0.08 })
        );
        const edges = new THREE.LineSegments(
          new THREE.EdgesGeometry(geometry, 15),
          new THREE.LineBasicMaterial({ color: "#1a2a4a" })
        );
        model = new THREE.Group();
        model.add(mesh);
        model.add(edges);
        model.rotation.x = -Math.PI / 2;
        scene.add(model);
        placeModelAtCornerOrigin(model, controls, camera);
      });
    } else if (previewUrl) {
      new GLTFLoader().load(previewUrl, (gltf) => {
        model = gltf.scene;
        model.traverse((child) => {
          if (child.isMesh) {
            child.material = new THREE.MeshStandardMaterial({ color: "#3b82f6", roughness: 0.55, metalness: 0.08 });
            child.add(new THREE.LineSegments(
              new THREE.EdgesGeometry(child.geometry, 15),
              new THREE.LineBasicMaterial({ color: "#1a2a4a" })
            ));
          }
        });
        model.rotation.x = -Math.PI / 2;
        scene.add(model);
        placeModelAtCornerOrigin(model, controls, camera);
      });
    }

    function resize() {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    }
    window.addEventListener("resize", resize);

    let frame = 0;
    function animate() {
      frame = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
      renderer.dispose();
      mount.replaceChildren();
    };
  }, [previewUrl, previewKind, selectedPlane]);

  return <div className="preview" ref={mountRef} />;
}

// ── Form helpers ──────────────────────────────────────────────────────────────

function Field({ label, value, onChange, type = "number", step = "0.1", min }) {
  return (
    <label>
      <span>{label}</span>
      <input type={type} step={step} min={min} value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

function SelectField({ label, value, onChange, children }) {
  return (
    <label>
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>{children}</select>
    </label>
  );
}

// ── Operation Block ───────────────────────────────────────────────────────────

function PlaneOperationBlock({ block, selected, onSelect, onChange, onDuplicate, onDelete, onMoveUp, onMoveDown }) {
  const isScrew = block.operation === "screw_hole";
  const isHole  = block.operation === "hole";
  const isBoss  = block.operation === "boss";
  const isConn  = block.operation === "connector";
  const isSolid = block.operation === "add_solid";

  // Shape dropdown config
  const showShapeDropdown = !isScrew && !isBoss;
  const shapeOptions = isHole ? SHAPES_HOLE : isConn ? SHAPES_CONNECTOR : isSolid ? SHAPES_SOLID : SHAPES_CUT;

  // Size controls visibility
  const isCircle = ["circle", "dc_jack"].includes(block.shape);
  const isRect   = ["rect", "rounded_rect", "usb_c", "usb_a", "hdmi"].includes(block.shape);
  const isSlot   = block.shape === "slot";

  const showDiameter   = !isScrew && !isBoss && isCircle && !isHole;
  const showHoleDia    = isHole && !isSlot;   // hole circle diameter
  const showSlotFields = isSlot;
  const showWH         = (isRect || isSolid) && !isScrew;
  const showCornerR    = ["rounded_rect", "usb_c", "usb_a", "hdmi"].includes(block.shape) && !isScrew;
  const hasSizeSection = showDiameter || showHoleDia || showSlotFields || showWH || isBoss;

  // Depth shown for everything except boss
  const showDepth = !isBoss;

  function set(field, value) { onChange({ ...block, [field]: value }); }
  function setCustom(field, value) { onChange({ ...block, customPlane: { ...block.customPlane, [field]: value } }); }

  function handleShapeChange(v) {
    if (isConn && CONNECTOR_DIMS[v]) {
      onChange({ ...block, shape: v, ...CONNECTOR_DIMS[v] });
    } else {
      set("shape", v);
    }
  }

  function handleOperationChange(op) {
    const shapeDefaults = { cut: "rect", screw_hole: "circle", connector: "usb_c", boss: "circle", add_solid: "rect" };
    const newShape = shapeDefaults[op] ?? "circle";
    const dims = (op === "connector" && CONNECTOR_DIMS[newShape]) ? CONNECTOR_DIMS[newShape] : {};
    onChange({ ...block, operation: op, shape: newShape, ...dims });
  }

  return (
    <section className={`operationBlock ${selected ? "selected" : ""}`} onClick={onSelect}>
      {/* ── Header ── */}
      <div className="blockHeader">
        <button
          className={block.enabled ? "iconToggle on" : "iconToggle"}
          onClick={(e) => { e.stopPropagation(); set("enabled", !block.enabled); }}
        >
          {block.enabled ? "On" : "Off"}
        </button>
        <input className="blockName" value={block.label} onChange={(e) => set("label", e.target.value)} />
        <button className="arrowBtn" title="Move up"   onClick={(e) => { e.stopPropagation(); onMoveUp();   }}>↑</button>
        <button className="arrowBtn" title="Move down" onClick={(e) => { e.stopPropagation(); onMoveDown(); }}>↓</button>
        <button onClick={(e) => { e.stopPropagation(); onDuplicate(); }}>Duplicate</button>
        <button className="quietDanger" onClick={(e) => { e.stopPropagation(); onDelete(); }}>Delete</button>
      </div>

      {/* ── Plane + Operation ── */}
      <div className="formGrid">
        <SelectField label="Plane" value={block.plane} onChange={(v) => set("plane", v)}>
          {FACES.map((f) => <option key={f} value={f}>{f === "custom" ? "Custom Plane" : f}</option>)}
        </SelectField>
        <SelectField label="Operation" value={block.operation} onChange={handleOperationChange}>
          {OPERATIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </SelectField>
      </div>

      {/* ── Custom Plane ── */}
      {block.plane === "custom" && (
        <div className="subPanel">
          <div className="subTitle">Custom Plane</div>
          <div className="formGrid compact">
            <Field label="Origin X" value={block.customPlane.originX} onChange={(v) => setCustom("originX", v)} />
            <Field label="Origin Y" value={block.customPlane.originY} onChange={(v) => setCustom("originY", v)} />
            <Field label="Origin Z" value={block.customPlane.originZ} onChange={(v) => setCustom("originZ", v)} />
            <Field label="Normal X" value={block.customPlane.normalX} onChange={(v) => setCustom("normalX", v)} />
            <Field label="Normal Y" value={block.customPlane.normalY} onChange={(v) => setCustom("normalY", v)} />
            <Field label="Normal Z" value={block.customPlane.normalZ} onChange={(v) => setCustom("normalZ", v)} />
            <Field label="Rotation°" value={block.customPlane.rotation} onChange={(v) => setCustom("rotation", v)} />
          </div>
        </div>
      )}

      {/* ── Position X Y ── */}
      <div className="subPanel" style={{ marginTop: 10 }}>
        <div className="subTitle" style={{ marginBottom: 8 }}>Position</div>
        <div className="formGrid">
          <Field label="X local (mm)" value={block.x} onChange={(v) => set("x", v)} />
          <Field label="Y local (mm)" value={block.y} onChange={(v) => set("y", v)} />
        </div>
      </div>

      {/* ── Shape / Cutout type (only when needed) ── */}
      {showShapeDropdown && (
        <div className="formGrid" style={{ marginTop: 10 }}>
          <SelectField label="Shape / cutout type" value={block.shape} onChange={handleShapeChange}>
            {shapeOptions.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </SelectField>
          {/* Depth mode alongside shape */}
          {showDepth && (
            <SelectField label="Depth mode" value={block.depthMode} onChange={(v) => set("depthMode", v)}>
              {DEPTH_MODES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </SelectField>
          )}
        </div>
      )}

      {/* Depth mode row for screw/boss (no shape dropdown) */}
      {!showShapeDropdown && showDepth && (
        <div className="formGrid" style={{ marginTop: 10 }}>
          <SelectField label="Depth mode" value={block.depthMode} onChange={(v) => set("depthMode", v)}>
            {DEPTH_MODES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </SelectField>
          {["blind", "custom"].includes(block.depthMode) && (
            <Field label="Depth (mm)" value={block.depth} onChange={(v) => set("depth", v)} min="0" />
          )}
        </div>
      )}
      {showShapeDropdown && ["blind", "custom"].includes(block.depthMode) && (
        <div className="formGrid" style={{ marginTop: 6 }}>
          <Field label="Depth (mm)" value={block.depth} onChange={(v) => set("depth", v)} min="0" />
          <div />
        </div>
      )}

      {/* ── Size Controls ── */}
      {hasSizeSection && (
        <div className="subPanel">
          <div className="subTitle">Size Controls</div>
          <div className="formGrid compact">
            {showDiameter   && <Field label="Diameter (mm)" value={block.diameter}   onChange={(v) => set("diameter", v)}   min="0.1" />}
            {showHoleDia    && <Field label="Diameter (mm)" value={block.diameter}   onChange={(v) => set("diameter", v)}   min="0.1" />}
            {showSlotFields && <Field label="Length (mm)"   value={block.slotLength} onChange={(v) => set("slotLength", v)} min="0.1" />}
            {showSlotFields && <Field label="Width (mm)"    value={block.slotWidth}  onChange={(v) => set("slotWidth", v)}  min="0.1" />}
            {showWH         && <Field label="Width (mm)"    value={block.width}      onChange={(v) => set("width", v)}      min="0.1" />}
            {showWH         && <Field label="Height (mm)"   value={block.height}     onChange={(v) => set("height", v)}     min="0.1" />}
            {showCornerR    && <Field label="Corner radius" value={block.cornerRadius} onChange={(v) => set("cornerRadius", v)} min="0" />}
            {isBoss         && <Field label="Outer ⌀ (mm)"  value={block.bossOuterDiameter} onChange={(v) => set("bossOuterDiameter", v)} min="0.1" />}
            {isBoss         && <Field label="Height (mm)"   value={block.bossHeight}         onChange={(v) => set("bossHeight", v)}         min="0.1" />}
            {isBoss         && <Field label="Inner ⌀ (mm)"  value={block.diameter}           onChange={(v) => set("diameter", v)}           min="0.1" />}
            {isSolid && ["blind","custom"].includes(block.depthMode) &&
              <Field label="Add solid depth" value={block.depth} onChange={(v) => set("depth", v)} min="0.1" />}
          </div>
        </div>
      )}

      {/* ── Screw Hole Wizard ── */}
      {isScrew && (() => {
        const ht = block.holeType || "clearance";
        const autoD = getScrewDims(ht, block.screwSize, block.fit || "normal");
        const dia    = block.showCustom ? block.diameter            : autoD.diameter;
        const cboreD = block.showCustom ? block.counterboreDiameter : autoD.counterboreDiameter;
        const cboreH = block.showCustom ? block.counterboreDepth    : autoD.counterboreDepth;
        const cskD   = block.showCustom ? block.countersinkDiameter : autoD.countersinkDiameter;
        const cskA   = block.showCustom ? block.countersinkAngle    : autoD.countersinkAngle;
        return (
          <div className="subPanel">
            <div className="subTitle">Screw Hole</div>

            {/* Hole type selector */}
            <div className="holeTypeRow">
              {HOLE_TYPES.map(({ id, label, desc }) => (
                <button
                  key={id}
                  className={"holeTypeBtn" + (ht === id ? " active" : "")}
                  title={desc}
                  onClick={(e) => { e.stopPropagation(); set("holeType", id); }}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Screw size + fit */}
            <div className="formGrid" style={{ marginTop: 8 }}>
              <SelectField label="Screw size" value={block.screwSize}
                onChange={(v) => set("screwSize", v)}>
                {SCREW_SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
              </SelectField>
              {ht !== "tapped" && (
                <SelectField label="Fit" value={block.fit || "normal"}
                  onChange={(v) => set("fit", v)}>
                  {FIT_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </SelectField>
              )}
            </div>

            {/* Dim summary */}
            <div className="dimSummary">
              <span>⌀ {dia?.toFixed ? dia.toFixed(2) : dia} mm</span>
              {ht === "counterbore" && <><span>Cbore ⌀ {cboreD?.toFixed ? cboreD.toFixed(1) : cboreD}</span><span>depth {cboreH?.toFixed ? cboreH.toFixed(1) : cboreH}</span></>}
              {ht === "countersink" && <><span>Csk ⌀ {cskD?.toFixed ? cskD.toFixed(1) : cskD}</span><span>{cskA}°</span></>}
            </div>

            {/* Custom sizing toggle */}
            <label className="checkboxRow" onClick={(e) => e.stopPropagation()}>
              <input type="checkbox" checked={!!block.showCustom}
                onChange={(e) => {
                  if (e.target.checked) {
                    const d = getScrewDims(ht, block.screwSize, block.fit || "normal");
                    onChange({ ...block, showCustom: true,
                      diameter:            d.diameter            ?? block.diameter,
                      counterboreDiameter: d.counterboreDiameter ?? block.counterboreDiameter,
                      counterboreDepth:    d.counterboreDepth    ?? block.counterboreDepth,
                      countersinkDiameter: d.countersinkDiameter ?? block.countersinkDiameter,
                      countersinkAngle:    d.countersinkAngle    ?? block.countersinkAngle,
                    });
                  } else { set("showCustom", false); }
                }}
              />
              Custom sizing
            </label>

            {block.showCustom && (
              <div className="formGrid compact" style={{ marginTop: 8 }}>
                <Field label="Hole ⌀ (mm)" value={block.diameter} onChange={(v) => set("diameter", v)} min="0.1" />
                {ht === "counterbore" && <>
                  <Field label="Cbore ⌀ (mm)"   value={block.counterboreDiameter} onChange={(v) => set("counterboreDiameter", v)} min="0" />
                  <Field label="Cbore depth"     value={block.counterboreDepth}    onChange={(v) => set("counterboreDepth", v)}    min="0" />
                </>}
                {ht === "countersink" && <>
                  <Field label="Csk ⌀ (mm)"    value={block.countersinkDiameter} onChange={(v) => set("countersinkDiameter", v)} min="0" />
                  <Field label="Csk angle°"     value={block.countersinkAngle}    onChange={(v) => set("countersinkAngle", v)} />
                </>}
              </div>
            )}
          </div>
        );
      })()}

      {/* ── Pattern ── */}
      <div className="subPanel">
        <div className="subTitle">Pattern / Quantity</div>
        <div className="formGrid compact">
          <SelectField label="Pattern" value={block.patternType} onChange={(v) => set("patternType", v)}>
            {PATTERNS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </SelectField>
          {block.patternType === "linear" && <>
            <Field label="Count"     step="1" value={block.linearCount}   onChange={(v) => set("linearCount", v)}   min="1" />
            <Field label="Spacing"            value={block.linearSpacing}  onChange={(v) => set("linearSpacing", v)}  min="0.1" />
            <Field label="Dir X"              value={block.directionX}     onChange={(v) => set("directionX", v)} />
            <Field label="Dir Y"              value={block.directionY}     onChange={(v) => set("directionY", v)} />
            <Field label="Dir Z"              value={block.directionZ}     onChange={(v) => set("directionZ", v)} />
          </>}
          {block.patternType === "grid" && <>
            <Field label="Rows"    step="1" value={block.rows}         onChange={(v) => set("rows", v)}         min="1" />
            <Field label="Columns" step="1" value={block.columns}      onChange={(v) => set("columns", v)}      min="1" />
            <Field label="Row spacing"       value={block.rowSpacing}   onChange={(v) => set("rowSpacing", v)}   min="0.1" />
            <Field label="Col spacing"       value={block.columnSpacing} onChange={(v) => set("columnSpacing", v)} min="0.1" />
          </>}
          {block.patternType === "circular" && <>
            <Field label="Count"   step="1" value={block.circularCount}  onChange={(v) => set("circularCount", v)}  min="1" />
            <Field label="Center X"         value={block.centerX}        onChange={(v) => set("centerX", v)} />
            <Field label="Center Y"         value={block.centerY}        onChange={(v) => set("centerY", v)} />
            <Field label="Radius"           value={block.circularRadius}  onChange={(v) => set("circularRadius", v)} min="0" />
            <Field label="Angle step°"      value={block.angleStep}       onChange={(v) => set("angleStep", v)} />
          </>}
        </div>
      </div>
    </section>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────

function App() {
  const [body, setBody]       = useState(starterBody);
  const [blocks, setBlocks]   = useState([createBlock(0), createBlock(1)]);
  const [selectedId, setSelectedId] = useState(null);
  const [status, setStatus]         = useState("Ready — click Preview to build");
  const [validationErrors, setValidationErrors] = useState([]);
  const [previewUrl, setPreviewUrl] = useState("");
  const [previewKind, setPreviewKind] = useState("glb");
  const [showJsonDebug, setShowJsonDebug] = useState(false);

  const project = useMemo(() => buildProject(body, blocks), [body, blocks]);
  const selectedBlock = blocks.find((b) => b.id === selectedId) || blocks[0];

  function updateBlock(id, next) { setBlocks((items) => updateArrayItem(items, id, () => next)); }

  function addBlock() {
    const b = createBlock(blocks.length);
    setBlocks((items) => [...items, b]);
    setSelectedId(b.id);
  }

  function moveBlock(id, dir) {
    setBlocks((items) => {
      const idx = items.findIndex((b) => b.id === id);
      if (idx < 0) return items;
      const next = [...items];
      const swap = idx + dir;
      if (swap < 0 || swap >= next.length) return items;
      [next[idx], next[swap]] = [next[swap], next[idx]];
      return next;
    });
  }

  async function postProject(path) {
    return fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project),
    });
  }

  async function validate() {
    setStatus("Validating…"); setValidationErrors([]);
    const res = await postProject("/api/validate");
    const data = await res.json();
    setValidationErrors(data.errors || []);
    setStatus(data.valid ? "✓ Valid" : "⚠ Validation issues");
    return data.valid;
  }

  async function preview() {
    setStatus("Building geometry…"); setValidationErrors([]);
    const res = await postProject("/api/preview");
    if (!res.ok) {
      const data = await res.json();
      setValidationErrors(data.detail?.errors || ["Preview failed"]);
      setStatus("Preview failed");
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewKind((res.headers.get("content-type") || "").includes("stl") ? "stl" : "glb");
    setPreviewUrl(URL.createObjectURL(await res.blob()));
    setStatus("Preview updated from backend geometry");
  }

  async function exportFormat(fmt) {
    setStatus(`Exporting ${fmt.toUpperCase()}…`);
    const res = await postProject(`/api/export/${fmt}`);
    if (!res.ok) {
      const data = await res.json();
      setValidationErrors(data.detail?.errors || ["Export failed"]);
      setStatus("Export failed"); return;
    }
    downloadBlob(await res.blob(), `${project.name}.${fmt}`);
    setStatus(`${fmt.toUpperCase()} exported`);
  }

  return (
    <main className="shell">
      {/* ── Toolbar ── */}
      <header className="toolbar">
        <strong>Parametric CAD</strong>
        <span className="toolbarMeta">Backend-generated geometry only</span>
        <div className="toolbarActions">
          <button onClick={validate}>Validate</button>
          <button className="previewBtn" onClick={preview}>▶ Preview / Update</button>
          <button onClick={() => exportFormat("step")}>Export STEP</button>
          <button onClick={() => exportFormat("stl")}>Export STL</button>
        </div>
        <span className={validationErrors.length ? "status bad" : "status"}>{status}</span>
      </header>

      <section className="workspace">
        {/* ── Canvas ── */}
        <section className="canvasRegion">
          <Preview previewUrl={previewUrl} previewKind={previewKind} selectedPlane={selectedBlock?.plane} />
          <div className="previewOverlay">
            <strong>{selectedBlock?.label || "No operation selected"}</strong>
            <span>{selectedBlock ? `${selectedBlock.plane} · ${selectedBlock.operation} · ${selectedBlock.patternType}` : "Add a plane operation"}</span>
          </div>
        </section>

        {/* ── Controls ── */}
        <aside className="controlsPanel">
          {/* Base Body */}
          <section className="bodyPanel">
            <div className="panelTitle">
              Base Body
              <button
                className={`solidToggle ${body.solid ? "on" : ""}`}
                onClick={() => setBody({ ...body, solid: !body.solid })}
                title="Toggle solid / hollow"
              >
                {body.solid ? "Solid" : "Hollow"}
              </button>
            </div>
            <div className="formGrid compact">
              <Field label="Name"   type="text" value={body.name}   onChange={(v) => setBody({ ...body, name: v })} />
              <Field label="Length" value={body.length} onChange={(v) => setBody({ ...body, length: v })} min="1" />
              <Field label="Width"  value={body.width}  onChange={(v) => setBody({ ...body, width: v })}  min="1" />
              <Field label="Height" value={body.height} onChange={(v) => setBody({ ...body, height: v })} min="1" />
              {!body.solid && <Field label="Wall"   value={body.wall}         onChange={(v) => setBody({ ...body, wall: v })}         min="0.1" />}
              <Field label="Fillet" value={body.fillet_radius} onChange={(v) => setBody({ ...body, fillet_radius: v })} min="0" />
            </div>
          </section>

          {/* Validation errors */}
          {validationErrors.length > 0 && (
            <div className="errorBox" style={{ marginBottom: 12 }}>
              {validationErrors.map((e) => <div key={e}>{e}</div>)}
            </div>
          )}

          {/* Operations */}
          <div className="blocksStack">
            {blocks.map((block) => (
              <PlaneOperationBlock
                key={block.id}
                block={block}
                selected={block.id === selectedId}
                onSelect={() => setSelectedId(block.id)}
                onChange={(next) => updateBlock(block.id, next)}
                onMoveUp={() => moveBlock(block.id, -1)}
                onMoveDown={() => moveBlock(block.id, 1)}
                onDuplicate={() => {
                  const clone = { ...structuredClone(block), id: `op_${Date.now()}`, label: `${block.label} Copy` };
                  setBlocks((items) => [...items, clone]);
                  setSelectedId(clone.id);
                }}
                onDelete={() => {
                  setBlocks((items) => {
                    const next = items.filter((b) => b.id !== block.id);
                    if (selectedId === block.id) setSelectedId(next[0]?.id || null);
                    return next.length ? next : [createBlock(0)];
                  });
                }}
              />
            ))}
            <button className="addBlockBtn" onClick={addBlock}>+ Add Plane Operation</button>
          </div>

          {/* JSON Debug */}
          <section className="debugPanel">
            <button onClick={() => setShowJsonDebug((o) => !o)}>
              {showJsonDebug ? "Hide JSON" : "Show JSON"}
            </button>
            {showJsonDebug && <pre>{JSON.stringify(project, null, 2)}</pre>}
          </section>
        </aside>
      </section>

      {/* ── Timeline Bar (Fusion 360-style) ── */}
      <aside className="historyBar">
        <span className="timelineLabel">Timeline</span>
        <div className="timelineStrip">
          {blocks.map((block) => (
            <button
              key={block.id}
              className={"timelineChip" + (block.id === selectedId ? " selected" : "") + (!block.enabled ? " suppressed" : "")}
              onClick={() => setSelectedId(block.id)}
              title={`${block.label}\n${block.plane} · ${block.operation} · ${block.patternType}`}
            >
              <span className="chipIcon">{OP_ICONS[block.operation] ?? "◈"}</span>
              <span className="chipName">{block.label}</span>
            </button>
          ))}
          <button className="timelineAdd" onClick={addBlock} title="Add operation">+</button>
        </div>
      </aside>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
