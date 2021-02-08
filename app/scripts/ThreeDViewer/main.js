import 'regenerator-runtime/runtime' // see: https://flaviocopes.com/parcel-regeneratorruntime-not-defined/
import CameraControls from 'camera-controls'
import * as holdEvent from 'hold-event'

const container = document.querySelector('#js-threedviewer__container')
const loadingStatus = document.querySelector('#js-threedviewer__loadstatus')
const loadingStatusLabel = document.querySelector('#js-threedviewer__loadstatus-label')
const loadingProgress = document.querySelector('#js-threedviewer__progressbar')
const loadingDownloadPercentLimit = 75

// Example glTF v.1 model using Basket 019:
const modelPath = 'https://dj5wl215uj1lm.cloudfront.net/video-test/Nuxeo/nxfile/default/f49e1cb8-0d9c-4dd8-8959-6eb7320a5a41/threed:transmissionFormats/4/content/transmissionformat-1404844697-50-1000000.gltf'

// Example glTF v.2 model using Space Shuttle Discovery:
// const modelPath = 'https://dj5wl215uj1lm.cloudfront.net/video-test/tests/test-shuttle.gltf'

const fetchModel = async function () {
  const response = await fetch(modelPath)

  if (!response.ok) {
    const message = `Object could not be loaded. HTTP error status: ${response.status}`
    loadingStatusLabel.innerText = message
    throw new Error(message)
  }

  // Read fetched stream of glTF model, show stream progress, build model buffer for glTF loader, and parse buffer as json for legacy/current model detection. Adapted from: https://javascript.info/fetch-progress:

  const reader = response.body.getReader()
  const contentLength = +response.headers.get('Content-Length')
  let receivedLength = 0
  const chunks = []

  while (true) {
    const { done, value } = await reader.read()

    if (done) {
      break
    }

    chunks.push(value)
    receivedLength += value.length

    loadingStatusLabel.innerText = 'Downloading object ...'
    loadingProgress.value = receivedLength / contentLength * loadingDownloadPercentLimit
  }

  const chunksAll = new Uint8Array(receivedLength)
  let position = 0

  for (const chunk of chunks) {
    chunksAll.set(chunk, position)
    position += chunk.length
  }

  const result = new TextDecoder('utf-8').decode(chunksAll)
  const modelBuffer = chunksAll.buffer
  const modelJson = await JSON.parse(result)

  let isLegacyThree
  let THREE
  let GLTFLoader

  // Load modules depending on if model glTF is version 1 or 2:

  if (modelJson.asset === undefined || modelJson.asset.version[0] < 2) {
    loadingStatusLabel.innerText = 'Reading object as glTF v.1 ...'
    isLegacyThree = true
    THREE = await import('three-v86')
    GLTFLoader = await import('./GLTFLoader1.js')
  } else {
    loadingStatusLabel.innerText = 'Reading object as glTF v.2 ...'
    isLegacyThree = false
    THREE = await import('three')
    GLTFLoader = await import('three/examples/jsm/loaders/GLTFLoader')
  }
  return [modelBuffer, isLegacyThree, THREE, GLTFLoader]
}

async function init () {
  const [modelBuffer, isLegacyThree, THREE, { GLTFLoader }] = await fetchModel()

  CameraControls.install({ THREE: THREE })

  /* Define Camera and Renderer */

  const scene = new THREE.Scene()

  const fov = 35
  const aspect = container.clientWidth / container.clientHeight
  const near = 0.1
  const far = 100

  const camera = new THREE.PerspectiveCamera(fov, aspect, near, far)

  camera.position.set(0, 0, 1)

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })

  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.setPixelRatio(window.devicePixelRatio)

  container.appendChild(renderer.domElement)

  const clock = new THREE.Clock()

  function render () {
    renderer.render(scene, camera)
  }

  function resizeContainer () {
    camera.aspect = container.clientWidth / container.clientHeight
    camera.updateProjectionMatrix()
    renderer.setSize(container.clientWidth, container.clientHeight)
    render()
  }

  window.addEventListener('resize', resizeContainer)

  /* Lights */

  const light = new THREE.AmbientLight(0x404040)

  scene.add(light)

  renderer.physicallyCorrectLights = true

  // Auto camera positioning with GLTF loader for displaying models at similar size in viewport. Adapted from: https://threejsfundamentals.org/threejs/lessons/threejs-load-gltf.html:

  function degToRad (degrees) {
    var pi = Math.PI
    return degrees * (pi / 180)
  }

  function frameArea (sizeToFitOnScreen, boxSize, boxCenter, camera) {
    const halfSizeToFitOnScreen = sizeToFitOnScreen * 0.5
    const halfFovY = degToRad(camera.fov * 0.5)
    const distance = halfSizeToFitOnScreen / Math.tan(halfFovY)

    const direction = (new THREE.Vector3())
      .subVectors(camera.position, boxCenter)
      .multiply(new THREE.Vector3(1, 0, 1))
      .normalize()

    camera.position.copy(direction.multiplyScalar(distance).add(boxCenter))
    camera.near = boxSize / 100
    camera.far = boxSize * 100
    camera.updateProjectionMatrix()
  }

  /* Model Loading Status */

  THREE.DefaultLoadingManager.onProgress = function (url, itemsLoaded, itemsTotal) {
    loadingStatusLabel.innerText = 'Loading object resources ...'
    loadingProgress.value = loadingDownloadPercentLimit + itemsLoaded / itemsTotal * 25
  }

  THREE.DefaultLoadingManager.onError = function (url) {
    loadingStatusLabel.innerText = 'Error loading object.'
  }

  const gltfLoader = new GLTFLoader()

  function loaderContents (gltf) {
    const root = gltf.scene

    scene.add(root)

    const box = new THREE.Box3().setFromObject(root)
    const boxSize = box.getSize(new THREE.Vector3()).length()
    const boxCenter = box.getCenter(new THREE.Vector3())

    frameArea(boxSize * 1, boxSize, boxCenter, camera)

    /* Camera Controls */

    const cameraControls = new CameraControls(camera, renderer.domElement)

    cameraControls.fitTo(box)
    cameraControls.rotateTo(30 * THREE.Math.DEG2RAD, 80 * THREE.Math.DEG2RAD)
    cameraControls.maxDistance = boxSize / 0.5

    const buttonReset = document.querySelector('#js-threedviewer__resetcamera')

    buttonReset.addEventListener('click', function () {
      cameraControls.rotateTo(0 * THREE.Math.DEG2RAD, 90 * THREE.Math.DEG2RAD, true)
      cameraControls.fitTo(box, true)
      cameraControls.rotateTo(30 * THREE.Math.DEG2RAD, 80 * THREE.Math.DEG2RAD, true)
      resizeContainer()
    })

    /* Keyboard Controls */

    const KEYCODE = {
      W: 87,
      A: 65,
      S: 83,
      D: 68,
      ARROW_LEFT: 37,
      ARROW_UP: 38,
      ARROW_RIGHT: 39,
      ARROW_DOWN: 40
    }

    // WASD keys for panning and zooming:

    const wKey = new holdEvent.KeyboardKeyHold(KEYCODE.W, 100)
    const aKey = new holdEvent.KeyboardKeyHold(KEYCODE.A, 100)
    const sKey = new holdEvent.KeyboardKeyHold(KEYCODE.S, 100)
    const dKey = new holdEvent.KeyboardKeyHold(KEYCODE.D, 100)
    wKey.addEventListener('holding', function (event) { cameraControls.forward(boxSize * 0.0005 * event.deltaTime, true) })
    aKey.addEventListener('holding', function (event) { cameraControls.truck(-boxSize * 0.0005 * event.deltaTime, 0, true) })
    sKey.addEventListener('holding', function (event) { cameraControls.forward(-boxSize * 0.0005 * event.deltaTime, true) })
    dKey.addEventListener('holding', function (event) { cameraControls.truck(boxSize * 0.0005 * event.deltaTime, 0, true) })

    // Arrow keys for rotating:

    const leftKey = new holdEvent.KeyboardKeyHold(KEYCODE.ARROW_LEFT, 100)
    const rightKey = new holdEvent.KeyboardKeyHold(KEYCODE.ARROW_RIGHT, 100)
    const upKey = new holdEvent.KeyboardKeyHold(KEYCODE.ARROW_UP, 100)
    const downKey = new holdEvent.KeyboardKeyHold(KEYCODE.ARROW_DOWN, 100)
    leftKey.addEventListener('holding', function (event) { cameraControls.rotate(-0.1 * THREE.Math.DEG2RAD * event.deltaTime, 0, true) })
    rightKey.addEventListener('holding', function (event) { cameraControls.rotate(0.1 * THREE.Math.DEG2RAD * event.deltaTime, 0, true) })
    upKey.addEventListener('holding', function (event) { cameraControls.rotate(0, -0.05 * THREE.Math.DEG2RAD * event.deltaTime, true) })
    downKey.addEventListener('holding', function (event) { cameraControls.rotate(0, 0.05 * THREE.Math.DEG2RAD * event.deltaTime, true) })

    /* Render Scene and Camera */

    render();

    (function anim () {
      const delta = clock.getDelta()
      const updated = cameraControls.update(delta)

      window.requestAnimationFrame(anim)

      if (updated) {
        loadingStatus.hidden = true
        render()
      }
    })()

    /* Light Intensity Control */

    function updateIntensity () {
      light.intensity = intensityRange.value
      render()
    }

    const intensityRange = document.querySelector('#js-threedviewer__intensityrange')

    if (isLegacyThree === false) {
      intensityRange.hidden = false
      intensityRange.addEventListener('input', updateIntensity)
      updateIntensity()
    }
  }

  if (isLegacyThree === true) {
    // Parse the buffered model using the legacy three.js loader parameters:

    gltfLoader.parse(modelBuffer, (gltf) => {
      loaderContents(gltf)
    })
  } else {
    // Parse the buffered model using the current three.js loader parameters:

    gltfLoader.parse(modelBuffer, '', (gltf) => {
      loaderContents(gltf)
    })
  }

  /* Fullscreen Control */

  const elFullscreen = document.querySelector('#js-threedviewer__container canvas')

  const buttonFullscreen = document.querySelector('#js-threedviewer__fullscreen')

  buttonFullscreen.addEventListener('click', function () {
    // Standard:
    if (elFullscreen.requestFullscreen) {
      elFullscreen.requestFullscreen()

    // Firefox:
    } else if (elFullscreen.mozRequestFullScreen) {
      elFullscreen.mozRequestFullScreen()

    // Chrome, Safari, and Opera:
    } else if (elFullscreen.webkitRequestFullscreen) {
      elFullscreen.webkitRequestFullscreen()

    // IE/Edge:
    } else if (elFullscreen.msRequestFullscreen) {
      elFullscreen.msRequestFullscreen()
    }
  })

  /* Directions Panel */

  function closeDirectionsPanel () {
    directionsPanel.hidden = true
    directionsToggle.setAttribute('aria-expanded', false)
    resizeContainer()
  }

  const directionsToggle = document.querySelector('#js-threedviewer__directions-toggle')
  const directionsPanel = document.querySelector('#js-threedviewer__directions-panel')
  const directionsPanelClose = document.querySelector('#js-threedviewer__directions-panel-close')

  directionsToggle.addEventListener('click', function () {
    if (directionsPanel.hidden === true) {
      directionsPanel.hidden = false
      directionsToggle.setAttribute('aria-expanded', true)
    } else {
      closeDirectionsPanel()
    }
  })

  directionsPanelClose.addEventListener('click', closeDirectionsPanel)
}

if (container) {
  init()
}
