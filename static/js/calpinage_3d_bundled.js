/**
 * @author qiao / https://github.com/qiao
 * @author mrdoob / http://mrdoob.com
 * @author alteredq / http://alteredqualia.com/
 * @author WestLangley / http://github.com/WestLangley
 * @author erich666 / http://erichaines.com
 */

// This set of controls performs orbiting, dollying (zooming), and panning.
// Unlike TrackballControls, it maintains the "up" direction object.up (+Y by default).
//
//    Orbit - left mouse / touch: one-finger move
//    Zoom - middle mouse, or mousewheel / touch: two-finger spread or squish
//    Pan - right mouse, or left mouse + ctrl/meta/shiftKey, or arrow keys / touch: two-finger move

THREE.OrbitControls = function ( object, domElement ) {

	this.object = object;

	this.domElement = ( domElement !== undefined ) ? domElement : document;

	// Set to false to disable this control
	this.enabled = true;

	// "target" sets the location of focus, where the object orbits around
	this.target = new THREE.Vector3();

	// How far you can dolly in and out ( PerspectiveCamera only )
	this.minDistance = 0;
	this.maxDistance = Infinity;

	// How far you can zoom in and out ( OrthographicCamera only )
	this.minZoom = 0;
	this.maxZoom = Infinity;

	// How far you can orbit vertically, upper and lower limits.
	// Range is 0 to Math.PI radians.
	this.minPolarAngle = 0; // radians
	this.maxPolarAngle = Math.PI; // radians

	// How far you can orbit horizontally, upper and lower limits.
	// If set, must be a sub-interval of the interval [ - Math.PI, Math.PI ].
	this.minAzimuthAngle = - Infinity; // radians
	this.maxAzimuthAngle = Infinity; // radians

	// Set to true to enable damping (inertia)
	// If damping is enabled, you must call controls.update() in your animation loop
	this.enableDamping = false;
	this.dampingFactor = 0.25;

	// This option actually enables dollying in and out; left as "zoom" for backwards compatibility.
	// Set to false to disable zooming
	this.enableZoom = true;
	this.zoomSpeed = 1.0;

	// Set to false to disable rotating
	this.enableRotate = true;
	this.rotateSpeed = 1.0;

	// Set to false to disable panning
	this.enablePan = true;
	this.panSpeed = 1.0;
	this.screenSpacePanning = false; // if true, pan in screen-space
	this.keyPanSpeed = 7.0;	// pixels moved per arrow key push

	// Set to true to automatically rotate around the target
	// If auto-rotate is enabled, you must call controls.update() in your animation loop
	this.autoRotate = false;
	this.autoRotateSpeed = 2.0; // 30 seconds per round when fps is 60

	// Set to false to disable use of the keys
	this.enableKeys = true;

	// The four arrow keys
	this.keys = { LEFT: 37, UP: 38, RIGHT: 39, BOTTOM: 40 };

	// Mouse buttons
	this.mouseButtons = { LEFT: THREE.MOUSE.LEFT, MIDDLE: THREE.MOUSE.MIDDLE, RIGHT: THREE.MOUSE.RIGHT };

	// for reset
	this.target0 = this.target.clone();
	this.position0 = this.object.position.clone();
	this.zoom0 = this.object.zoom;

	//
	// public methods
	//

	this.getPolarAngle = function () {

		return spherical.phi;

	};

	this.getAzimuthalAngle = function () {

		return spherical.theta;

	};

	this.saveState = function () {

		scope.target0.copy( scope.target );
		scope.position0.copy( scope.object.position );
		scope.zoom0 = scope.object.zoom;

	};

	this.reset = function () {

		scope.target.copy( scope.target0 );
		scope.object.position.copy( scope.position0 );
		scope.object.zoom = scope.zoom0;

		scope.object.updateProjectionMatrix();
		scope.dispatchEvent( changeEvent );

		scope.update();

		state = STATE.NONE;

	};

	// this method is exposed, but perhaps it would be better if we can make it private...
	this.update = function () {

		var offset = new THREE.Vector3();

		// so camera.up is the orbit axis
		var quat = new THREE.Quaternion().setFromUnitVectors( object.up, new THREE.Vector3( 0, 1, 0 ) );
		var quatInverse = quat.clone().inverse();

		var lastPosition = new THREE.Vector3();
		var lastQuaternion = new THREE.Quaternion();

		return function update() {

			var position = scope.object.position;

			offset.copy( position ).sub( scope.target );

			// rotate offset to "y-axis-is-up" space
			offset.applyQuaternion( quat );

			// angle from z-axis around y-axis
			spherical.setFromVector3( offset );

			if ( scope.autoRotate && state === STATE.NONE ) {

				rotateLeft( getAutoRotationAngle() );

			}

			spherical.theta += sphericalDelta.theta;
			spherical.phi += sphericalDelta.phi;

			// restrict theta to be between desired limits
			spherical.theta = Math.max( scope.minAzimuthAngle, Math.min( scope.maxAzimuthAngle, spherical.theta ) );

			// restrict phi to be between desired limits
			spherical.phi = Math.max( scope.minPolarAngle, Math.min( scope.maxPolarAngle, spherical.phi ) );

			spherical.makeSafe();


			spherical.radius *= scale;

			// restrict radius to be between desired limits
			spherical.radius = Math.max( scope.minDistance, Math.min( scope.maxDistance, spherical.radius ) );

			// move target to panned location
			scope.target.add( panOffset );

			offset.setFromSpherical( spherical );

			// rotate offset back to "camera-up-vector-is-up" space
			offset.applyQuaternion( quatInverse );

			position.copy( scope.target ).add( offset );

			scope.object.lookAt( scope.target );

			if ( scope.enableDamping === true ) {

				sphericalDelta.theta *= ( 1 - scope.dampingFactor );
				sphericalDelta.phi *= ( 1 - scope.dampingFactor );

				panOffset.multiplyScalar( 1 - scope.dampingFactor );

			} else {

				sphericalDelta.set( 0, 0, 0 );

				panOffset.set( 0, 0, 0 );

			}

			scale = 1;

			// update condition is:
			// min(camera displacement, camera rotation in radians)^2 > EPS
			// using small-angle approximation cos(x/2) = 1 - x^2 / 8

			if ( zoomChanged ||
				lastPosition.distanceToSquared( scope.object.position ) > EPS ||
				8 * ( 1 - lastQuaternion.dot( scope.object.quaternion ) ) > EPS ) {

				scope.dispatchEvent( changeEvent );

				lastPosition.copy( scope.object.position );
				lastQuaternion.copy( scope.object.quaternion );
				zoomChanged = false;

				return true;

			}

			return false;

		};

	}();

	this.dispose = function () {

		scope.domElement.removeEventListener( 'contextmenu', onContextMenu, false );
		scope.domElement.removeEventListener( 'mousedown', onMouseDown, false );
		scope.domElement.removeEventListener( 'wheel', onMouseWheel, false );

		scope.domElement.removeEventListener( 'touchstart', onTouchStart, false );
		scope.domElement.removeEventListener( 'touchend', onTouchEnd, false );
		scope.domElement.removeEventListener( 'touchmove', onTouchMove, false );

		document.removeEventListener( 'mousemove', onMouseMove, false );
		document.removeEventListener( 'mouseup', onMouseUp, false );

		window.removeEventListener( 'keydown', onKeyDown, false );

		//scope.dispatchEvent( { type: 'dispose' } ); // should this be added here?

	};

	//
	// internals
	//

	var scope = this;

	var changeEvent = { type: 'change' };
	var startEvent = { type: 'start' };
	var endEvent = { type: 'end' };

	var STATE = { NONE: - 1, ROTATE: 0, DOLLY: 1, PAN: 2, TOUCH_ROTATE: 3, TOUCH_DOLLY_PAN: 4 };

	var state = STATE.NONE;

	var EPS = 0.000001;

	// current position in spherical coordinates
	var spherical = new THREE.Spherical();
	var sphericalDelta = new THREE.Spherical();

	var scale = 1;
	var panOffset = new THREE.Vector3();
	var zoomChanged = false;

	var rotateStart = new THREE.Vector2();
	var rotateEnd = new THREE.Vector2();
	var rotateDelta = new THREE.Vector2();

	var panStart = new THREE.Vector2();
	var panEnd = new THREE.Vector2();
	var panDelta = new THREE.Vector2();

	var dollyStart = new THREE.Vector2();
	var dollyEnd = new THREE.Vector2();
	var dollyDelta = new THREE.Vector2();

	function getAutoRotationAngle() {

		return 2 * Math.PI / 60 / 60 * scope.autoRotateSpeed;

	}

	function getZoomScale() {

		return Math.pow( 0.95, scope.zoomSpeed );

	}

	function rotateLeft( angle ) {

		sphericalDelta.theta -= angle;

	}

	function rotateUp( angle ) {

		sphericalDelta.phi -= angle;

	}

	var panLeft = function () {

		var v = new THREE.Vector3();

		return function panLeft( distance, objectMatrix ) {

			v.setFromMatrixColumn( objectMatrix, 0 ); // get X column of objectMatrix
			v.multiplyScalar( - distance );

			panOffset.add( v );

		};

	}();

	var panUp = function () {

		var v = new THREE.Vector3();

		return function panUp( distance, objectMatrix ) {

			if ( scope.screenSpacePanning === true ) {

				v.setFromMatrixColumn( objectMatrix, 1 );

			} else {

				v.setFromMatrixColumn( objectMatrix, 0 );
				v.crossVectors( scope.object.up, v );

			}

			v.multiplyScalar( distance );

			panOffset.add( v );

		};

	}();

	// deltaX and deltaY are in pixels; right and down are positive
	var pan = function () {

		var offset = new THREE.Vector3();

		return function pan( deltaX, deltaY ) {

			var element = scope.domElement === document ? scope.domElement.body : scope.domElement;

			if ( scope.object.isPerspectiveCamera ) {

				// perspective
				var position = scope.object.position;
				offset.copy( position ).sub( scope.target );
				var targetDistance = offset.length();

				// half of the fov is center to top of screen
				targetDistance *= Math.tan( ( scope.object.fov / 2 ) * Math.PI / 180.0 );

				// we use only clientHeight here so aspect ratio does not distort speed
				panLeft( 2 * deltaX * targetDistance / element.clientHeight, scope.object.matrix );
				panUp( 2 * deltaY * targetDistance / element.clientHeight, scope.object.matrix );

			} else if ( scope.object.isOrthographicCamera ) {

				// orthographic
				panLeft( deltaX * ( scope.object.right - scope.object.left ) / scope.object.zoom / element.clientWidth, scope.object.matrix );
				panUp( deltaY * ( scope.object.top - scope.object.bottom ) / scope.object.zoom / element.clientHeight, scope.object.matrix );

			} else {

				// camera neither orthographic nor perspective
				console.warn( 'WARNING: OrbitControls.js encountered an unknown camera type - pan disabled.' );
				scope.enablePan = false;

			}

		};

	}();

	function dollyIn( dollyScale ) {

		if ( scope.object.isPerspectiveCamera ) {

			scale /= dollyScale;

		} else if ( scope.object.isOrthographicCamera ) {

			scope.object.zoom = Math.max( scope.minZoom, Math.min( scope.maxZoom, scope.object.zoom * dollyScale ) );
			scope.object.updateProjectionMatrix();
			zoomChanged = true;

		} else {

			console.warn( 'WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled.' );
			scope.enableZoom = false;

		}

	}

	function dollyOut( dollyScale ) {

		if ( scope.object.isPerspectiveCamera ) {

			scale *= dollyScale;

		} else if ( scope.object.isOrthographicCamera ) {

			scope.object.zoom = Math.max( scope.minZoom, Math.min( scope.maxZoom, scope.object.zoom / dollyScale ) );
			scope.object.updateProjectionMatrix();
			zoomChanged = true;

		} else {

			console.warn( 'WARNING: OrbitControls.js encountered an unknown camera type - dolly/zoom disabled.' );
			scope.enableZoom = false;

		}

	}

	//
	// event callbacks - update the object state
	//

	function handleMouseDownRotate( event ) {

		//console.log( 'handleMouseDownRotate' );

		rotateStart.set( event.clientX, event.clientY );

	}

	function handleMouseDownDolly( event ) {

		//console.log( 'handleMouseDownDolly' );

		dollyStart.set( event.clientX, event.clientY );

	}

	function handleMouseDownPan( event ) {

		//console.log( 'handleMouseDownPan' );

		panStart.set( event.clientX, event.clientY );

	}

	function handleMouseMoveRotate( event ) {

		//console.log( 'handleMouseMoveRotate' );

		rotateEnd.set( event.clientX, event.clientY );

		rotateDelta.subVectors( rotateEnd, rotateStart ).multiplyScalar( scope.rotateSpeed );

		var element = scope.domElement === document ? scope.domElement.body : scope.domElement;

		rotateLeft( 2 * Math.PI * rotateDelta.x / element.clientHeight ); // yes, height

		rotateUp( 2 * Math.PI * rotateDelta.y / element.clientHeight );

		rotateStart.copy( rotateEnd );

		scope.update();

	}

	function handleMouseMoveDolly( event ) {

		//console.log( 'handleMouseMoveDolly' );

		dollyEnd.set( event.clientX, event.clientY );

		dollyDelta.subVectors( dollyEnd, dollyStart );

		if ( dollyDelta.y > 0 ) {

			dollyIn( getZoomScale() );

		} else if ( dollyDelta.y < 0 ) {

			dollyOut( getZoomScale() );

		}

		dollyStart.copy( dollyEnd );

		scope.update();

	}

	function handleMouseMovePan( event ) {

		//console.log( 'handleMouseMovePan' );

		panEnd.set( event.clientX, event.clientY );

		panDelta.subVectors( panEnd, panStart ).multiplyScalar( scope.panSpeed );

		pan( panDelta.x, panDelta.y );

		panStart.copy( panEnd );

		scope.update();

	}

	function handleMouseUp( event ) {

		// console.log( 'handleMouseUp' );

	}

	function handleMouseWheel( event ) {

		// console.log( 'handleMouseWheel' );

		if ( event.deltaY < 0 ) {

			dollyOut( getZoomScale() );

		} else if ( event.deltaY > 0 ) {

			dollyIn( getZoomScale() );

		}

		scope.update();

	}

	function handleKeyDown( event ) {

		//console.log( 'handleKeyDown' );

		switch ( event.keyCode ) {

			case scope.keys.UP:
				pan( 0, scope.keyPanSpeed );
				scope.update();
				break;

			case scope.keys.BOTTOM:
				pan( 0, - scope.keyPanSpeed );
				scope.update();
				break;

			case scope.keys.LEFT:
				pan( scope.keyPanSpeed, 0 );
				scope.update();
				break;

			case scope.keys.RIGHT:
				pan( - scope.keyPanSpeed, 0 );
				scope.update();
				break;

		}

	}

	function handleTouchStartRotate( event ) {

		//console.log( 'handleTouchStartRotate' );

		rotateStart.set( event.touches[ 0 ].pageX, event.touches[ 0 ].pageY );

	}

	function handleTouchStartDollyPan( event ) {

		//console.log( 'handleTouchStartDollyPan' );

		if ( scope.enableZoom ) {

			var dx = event.touches[ 0 ].pageX - event.touches[ 1 ].pageX;
			var dy = event.touches[ 0 ].pageY - event.touches[ 1 ].pageY;

			var distance = Math.sqrt( dx * dx + dy * dy );

			dollyStart.set( 0, distance );

		}

		if ( scope.enablePan ) {

			var x = 0.5 * ( event.touches[ 0 ].pageX + event.touches[ 1 ].pageX );
			var y = 0.5 * ( event.touches[ 0 ].pageY + event.touches[ 1 ].pageY );

			panStart.set( x, y );

		}

	}

	function handleTouchMoveRotate( event ) {

		//console.log( 'handleTouchMoveRotate' );

		rotateEnd.set( event.touches[ 0 ].pageX, event.touches[ 0 ].pageY );

		rotateDelta.subVectors( rotateEnd, rotateStart ).multiplyScalar( scope.rotateSpeed );

		var element = scope.domElement === document ? scope.domElement.body : scope.domElement;

		rotateLeft( 2 * Math.PI * rotateDelta.x / element.clientHeight ); // yes, height

		rotateUp( 2 * Math.PI * rotateDelta.y / element.clientHeight );

		rotateStart.copy( rotateEnd );

		scope.update();

	}

	function handleTouchMoveDollyPan( event ) {

		//console.log( 'handleTouchMoveDollyPan' );

		if ( scope.enableZoom ) {

			var dx = event.touches[ 0 ].pageX - event.touches[ 1 ].pageX;
			var dy = event.touches[ 0 ].pageY - event.touches[ 1 ].pageY;

			var distance = Math.sqrt( dx * dx + dy * dy );

			dollyEnd.set( 0, distance );

			dollyDelta.set( 0, Math.pow( dollyEnd.y / dollyStart.y, scope.zoomSpeed ) );

			dollyIn( dollyDelta.y );

			dollyStart.copy( dollyEnd );

		}

		if ( scope.enablePan ) {

			var x = 0.5 * ( event.touches[ 0 ].pageX + event.touches[ 1 ].pageX );
			var y = 0.5 * ( event.touches[ 0 ].pageY + event.touches[ 1 ].pageY );

			panEnd.set( x, y );

			panDelta.subVectors( panEnd, panStart ).multiplyScalar( scope.panSpeed );

			pan( panDelta.x, panDelta.y );

			panStart.copy( panEnd );

		}

		scope.update();

	}

	function handleTouchEnd( event ) {

		//console.log( 'handleTouchEnd' );

	}

	//
	// event handlers - FSM: listen for events and reset state
	//

	function onMouseDown( event ) {

		if ( scope.enabled === false ) return;

		event.preventDefault();

		switch ( event.button ) {

			case scope.mouseButtons.LEFT:

				if ( event.ctrlKey || event.metaKey || event.shiftKey ) {

					if ( scope.enablePan === false ) return;

					handleMouseDownPan( event );

					state = STATE.PAN;

				} else {

					if ( scope.enableRotate === false ) return;

					handleMouseDownRotate( event );

					state = STATE.ROTATE;

				}

				break;

			case scope.mouseButtons.MIDDLE:

				if ( scope.enableZoom === false ) return;

				handleMouseDownDolly( event );

				state = STATE.DOLLY;

				break;

			case scope.mouseButtons.RIGHT:

				if ( scope.enablePan === false ) return;

				handleMouseDownPan( event );

				state = STATE.PAN;

				break;

		}

		if ( state !== STATE.NONE ) {

			document.addEventListener( 'mousemove', onMouseMove, false );
			document.addEventListener( 'mouseup', onMouseUp, false );

			scope.dispatchEvent( startEvent );

		}

	}

	function onMouseMove( event ) {

		if ( scope.enabled === false ) return;

		event.preventDefault();

		switch ( state ) {

			case STATE.ROTATE:

				if ( scope.enableRotate === false ) return;

				handleMouseMoveRotate( event );

				break;

			case STATE.DOLLY:

				if ( scope.enableZoom === false ) return;

				handleMouseMoveDolly( event );

				break;

			case STATE.PAN:

				if ( scope.enablePan === false ) return;

				handleMouseMovePan( event );

				break;

		}

	}

	function onMouseUp( event ) {

		if ( scope.enabled === false ) return;

		handleMouseUp( event );

		document.removeEventListener( 'mousemove', onMouseMove, false );
		document.removeEventListener( 'mouseup', onMouseUp, false );

		scope.dispatchEvent( endEvent );

		state = STATE.NONE;

	}

	function onMouseWheel( event ) {

		if ( scope.enabled === false || scope.enableZoom === false || ( state !== STATE.NONE && state !== STATE.ROTATE ) ) return;

		event.preventDefault();
		event.stopPropagation();

		scope.dispatchEvent( startEvent );

		handleMouseWheel( event );

		scope.dispatchEvent( endEvent );

	}

	function onKeyDown( event ) {

		if ( scope.enabled === false || scope.enableKeys === false || scope.enablePan === false ) return;

		handleKeyDown( event );

	}

	function onTouchStart( event ) {

		if ( scope.enabled === false ) return;

		event.preventDefault();

		switch ( event.touches.length ) {

			case 1:	// one-fingered touch: rotate

				if ( scope.enableRotate === false ) return;

				handleTouchStartRotate( event );

				state = STATE.TOUCH_ROTATE;

				break;

			case 2:	// two-fingered touch: dolly-pan

				if ( scope.enableZoom === false && scope.enablePan === false ) return;

				handleTouchStartDollyPan( event );

				state = STATE.TOUCH_DOLLY_PAN;

				break;

			default:

				state = STATE.NONE;

		}

		if ( state !== STATE.NONE ) {

			scope.dispatchEvent( startEvent );

		}

	}

	function onTouchMove( event ) {

		if ( scope.enabled === false ) return;

		event.preventDefault();
		event.stopPropagation();

		switch ( event.touches.length ) {

			case 1: // one-fingered touch: rotate

				if ( scope.enableRotate === false ) return;
				if ( state !== STATE.TOUCH_ROTATE ) return; // is this needed?

				handleTouchMoveRotate( event );

				break;

			case 2: // two-fingered touch: dolly-pan

				if ( scope.enableZoom === false && scope.enablePan === false ) return;
				if ( state !== STATE.TOUCH_DOLLY_PAN ) return; // is this needed?

				handleTouchMoveDollyPan( event );

				break;

			default:

				state = STATE.NONE;

		}

	}

	function onTouchEnd( event ) {

		if ( scope.enabled === false ) return;

		handleTouchEnd( event );

		scope.dispatchEvent( endEvent );

		state = STATE.NONE;

	}

	function onContextMenu( event ) {

		if ( scope.enabled === false ) return;

		event.preventDefault();

	}

	//

	scope.domElement.addEventListener( 'contextmenu', onContextMenu, false );

	scope.domElement.addEventListener( 'mousedown', onMouseDown, false );
	scope.domElement.addEventListener( 'wheel', onMouseWheel, false );

	scope.domElement.addEventListener( 'touchstart', onTouchStart, false );
	scope.domElement.addEventListener( 'touchend', onTouchEnd, false );
	scope.domElement.addEventListener( 'touchmove', onTouchMove, false );

	window.addEventListener( 'keydown', onKeyDown, false );

	// force an update at start

	this.update();

};

THREE.OrbitControls.prototype = Object.create( THREE.EventDispatcher.prototype );
THREE.OrbitControls.prototype.constructor = THREE.OrbitControls;

Object.defineProperties( THREE.OrbitControls.prototype, {

	center: {

		get: function () {

			console.warn( 'THREE.OrbitControls: .center has been renamed to .target' );
			return this.target;

		}

	},

	// backward compatibility

	noZoom: {

		get: function () {

			console.warn( 'THREE.OrbitControls: .noZoom has been deprecated. Use .enableZoom instead.' );
			return ! this.enableZoom;

		},

		set: function ( value ) {

			console.warn( 'THREE.OrbitControls: .noZoom has been deprecated. Use .enableZoom instead.' );
			this.enableZoom = ! value;

		}

	},

	noRotate: {

		get: function () {

			console.warn( 'THREE.OrbitControls: .noRotate has been deprecated. Use .enableRotate instead.' );
			return ! this.enableRotate;

		},

		set: function ( value ) {

			console.warn( 'THREE.OrbitControls: .noRotate has been deprecated. Use .enableRotate instead.' );
			this.enableRotate = ! value;

		}

	},

	noPan: {

		get: function () {

			console.warn( 'THREE.OrbitControls: .noPan has been deprecated. Use .enablePan instead.' );
			return ! this.enablePan;

		},

		set: function ( value ) {

			console.warn( 'THREE.OrbitControls: .noPan has been deprecated. Use .enablePan instead.' );
			this.enablePan = ! value;

		}

	},

	noKeys: {

		get: function () {

			console.warn( 'THREE.OrbitControls: .noKeys has been deprecated. Use .enableKeys instead.' );
			return ! this.enableKeys;

		},

		set: function ( value ) {

			console.warn( 'THREE.OrbitControls: .noKeys has been deprecated. Use .enableKeys instead.' );
			this.enableKeys = ! value;

		}

	},

	staticMoving: {

		get: function () {

			console.warn( 'THREE.OrbitControls: .staticMoving has been deprecated. Use .enableDamping instead.' );
			return ! this.enableDamping;

		},

		set: function ( value ) {

			console.warn( 'THREE.OrbitControls: .staticMoving has been deprecated. Use .enableDamping instead.' );
			this.enableDamping = ! value;

		}

	},

	dynamicDampingFactor: {

		get: function () {

			console.warn( 'THREE.OrbitControls: .dynamicDampingFactor has been renamed. Use .dampingFactor instead.' );
			return this.dampingFactor;

		},

		set: function ( value ) {

			console.warn( 'THREE.OrbitControls: .dynamicDampingFactor has been renamed. Use .dampingFactor instead.' );
			this.dampingFactor = value;

		}

	}

} );
/**
 * Module de visualisation 3D WebGL pour le calpinage PV
 * Utilise Three.js pour afficher les toitures et modules en 3D
 */

class Calpinage3DViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.modules3D = [];
        this.building3D = null;
        this.sunLight = null;
        this.isActive = false;
        
        // Configuration
        this.moduleThickness = 0.04; // 4cm d'épaisseur pour les modules
        this.buildingHeight = 8; // Hauteur par défaut du bâtiment (mètres)
    }
    
    /**
     * Initialiser la scène 3D
     */
    init() {
        if (this.isActive) return;
        
        console.log('🌐 Initialisation de la vue 3D WebGL...');
        
        // Créer la scène
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x87ceeb); // Bleu ciel
        this.scene.fog = new THREE.Fog(0x87ceeb, 100, 500);
        
        // Caméra perspective
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
        this.camera.position.set(50, 40, 50);
        this.camera.lookAt(0, 0, 0);
        
        // Renderer WebGL avec antialiasing
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.0;
        
        this.container.appendChild(this.renderer.domElement);
        
        // Contrôles orbitaux (rotation, zoom, pan)
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxPolarAngle = Math.PI / 2; // Empêcher de passer sous le sol
        this.controls.minDistance = 10;
        this.controls.maxDistance = 200;
        
        // Lumières
        this.setupLights();
        
        // Sol (grille)
        this.addGround();
        
        // Axes de référence (debug)
        const axesHelper = new THREE.AxesHelper(20);
        this.scene.add(axesHelper);
        
        // Gestion du redimensionnement
        window.addEventListener('resize', () => this.onWindowResize(), false);
        
        // Démarrer l'animation
        this.animate();
        
        this.isActive = true;
        console.log('✅ Vue 3D initialisée avec succès');
    }
    
    /**
     * Configuration des lumières
     */
    setupLights() {
        // Lumière ambiante (éclairage général)
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);
        
        // Soleil (lumière directionnelle avec ombres)
        this.sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
        this.sunLight.position.set(50, 80, 50);
        this.sunLight.castShadow = true;
        
        // Configuration des ombres
        this.sunLight.shadow.mapSize.width = 2048;
        this.sunLight.shadow.mapSize.height = 2048;
        this.sunLight.shadow.camera.near = 0.5;
        this.sunLight.shadow.camera.far = 500;
        this.sunLight.shadow.camera.left = -100;
        this.sunLight.shadow.camera.right = 100;
        this.sunLight.shadow.camera.top = 100;
        this.sunLight.shadow.camera.bottom = -100;
        
        this.scene.add(this.sunLight);
        
        // Helper pour visualiser la direction du soleil (debug)
        // const sunHelper = new THREE.DirectionalLightHelper(this.sunLight, 5);
        // this.scene.add(sunHelper);
        
        // Lumière hémisphérique (ciel/sol)
        const hemiLight = new THREE.HemisphereLight(0x87ceeb, 0x6b8e23, 0.3);
        this.scene.add(hemiLight);
    }
    
    /**
     * Ajouter un sol avec grille
     */
    addGround() {
        // Grille au sol (semi-transparente)
        const gridHelper = new THREE.GridHelper(200, 40, 0x888888, 0xcccccc);
        gridHelper.material.opacity = 0.25;
        gridHelper.material.transparent = true;
        this.scene.add(gridHelper);
        
        // Plan au sol (pour recevoir les ombres et la texture satellite)
        const groundGeometry = new THREE.PlaneGeometry(200, 200);
        const groundMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xffffff,
            roughness: 0.9,
            metalness: 0.1
        });
        this.ground = new THREE.Mesh(groundGeometry, groundMaterial);
        this.ground.rotation.x = -Math.PI / 2;
        this.ground.receiveShadow = true;
        this.scene.add(this.ground);
    }
    
    /**
     * Charger l'image satellite comme texture du sol
     */
    loadSatelliteTexture(imageUrl, bounds) {
        if (!this.ground) {
            console.warn('⚠️ [3D] Pas de ground pour la texture');
            return;
        }
        
        if (!imageUrl || imageUrl.length < 100) {
            console.error('❌ [3D] Image URL invalide:', imageUrl?.substring(0, 50));
            return;
        }
        
        console.log('🛰️ [3D] Chargement texture satellite...');
        console.log('   Bounds:', bounds);
        console.log('   Image size:', (imageUrl.length / 1024).toFixed(0), 'KB');
        
        // Créer une image directement (plus simple que TextureLoader)
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        img.onload = () => {
            console.log('✅ Image chargée:', img.width, 'x', img.height);
            
            const texture = new THREE.Texture(img);
            texture.wrapS = THREE.ClampToEdgeWrapping;
            texture.wrapT = THREE.ClampToEdgeWrapping;
            texture.encoding = THREE.sRGBEncoding;
            texture.minFilter = THREE.LinearFilter;
            texture.magFilter = THREE.LinearFilter;
            texture.needsUpdate = true;
            
            // Calculer la taille du sol en fonction des bounds
            if (bounds && bounds.swLat && bounds.neLat) {
                const latRef = (bounds.swLat + bounds.neLat) / 2;
                const metersPerDegreeLat = 111320;
                const metersPerDegreeLng = 111320 * Math.cos(latRef * Math.PI / 180);
                
                const width = Math.abs(bounds.neLng - bounds.swLng) * metersPerDegreeLng;
                const height = Math.abs(bounds.neLat - bounds.swLat) * metersPerDegreeLat;
                
                console.log(`📏 Redimensionnement sol: ${width.toFixed(0)}m x ${height.toFixed(0)}m`);
                
                // Redimensionner le sol pour correspondre à la texture
                this.ground.geometry.dispose();
                this.ground.geometry = new THREE.PlaneGeometry(width, height);
            }
            
            // Appliquer au sol
            if (this.ground.material.map) {
                this.ground.material.map.dispose();
            }
            this.ground.material.map = texture;
            this.ground.material.needsUpdate = true;
            
            console.log('✅ [3D] Texture satellite appliquée au sol');
        };
        
        img.onerror = (error) => {
            console.error('❌ [3D] Erreur chargement image:', error);
            console.error('   URL length:', imageUrl.length);
        };
        
        img.src = imageUrl;
    }
    
    /**
     * Créer structure ombrière de parking avec normes
     * Normes parking: 5m largeur x 2.5m profondeur par place
     * Structure: piliers tous les 5m, pannes tous les 2.5m, fermes triangulaires
     */
    createOmbriereStructure(zone) {
        const bounds = zone.layer.getBounds();
        const center = bounds.getCenter();
        const centerMeters = this.latLngToMeters(center.lat, center.lng);
        
        // Dimensions de la zone en mètres
        const width = zone.largeurMetres;
        const depth = zone.longueurMetres;
        
        // Récupérer les paramètres depuis l'interface (avec valeurs par défaut)
        const placeWidth = parseFloat(document.getElementById('ombriereLargeurPlace')?.value || 2.5);
        const placeDepth = parseFloat(document.getElementById('ombriereProfondeurPlace')?.value || 5.0);
        const hauteurPilier = parseFloat(document.getElementById('ombriereHauteur')?.value || 4.5);
        const hauteurFerme = parseFloat(document.getElementById('ombriereHauteurFerme')?.value || 0.8);
        const pilierRadius = parseFloat(document.getElementById('ombriereDiametrePilier')?.value || 15) / 200; // cm -> m (rayon)
        const panneWidth = parseFloat(document.getElementById('ombriereSectionPanne')?.value || 10) / 100; // cm -> m
        const fermeWidth = parseFloat(document.getElementById('ombriereSectionFerme')?.value || 8) / 100; // cm -> m
        
        console.log(`🅿️ Paramètres ombrière: Place ${placeWidth}×${placeDepth}m, H=${hauteurPilier}m, Pilier Ø${pilierRadius*2}m`);
        
        // Matériaux
        const metalMaterial = new THREE.MeshStandardMaterial({
            color: 0x505050,
            metalness: 0.8,
            roughness: 0.3
        });
        
        // Groupe pour toute la structure
        const structureGroup = new THREE.Group();
        
        // 1. PILIERS CENTRAUX (tous les placeDepth en profondeur, tous les placeWidth en largeur)
        const nbPiliersDepth = Math.floor(depth / placeDepth) + 1;
        const nbPiliersWidth = Math.floor(width / placeWidth) + 1;
        
        const pilierGeometry = new THREE.CylinderGeometry(pilierRadius, pilierRadius, hauteurPilier, 8);
        
        for (let i = 0; i < nbPiliersDepth; i++) {
            for (let j = 0; j < nbPiliersWidth; j++) {
                const x = -width/2 + j * placeWidth;
                const z = -depth/2 + i * placeDepth;
                
                const pilier = new THREE.Mesh(pilierGeometry, metalMaterial);
                pilier.position.set(
                    centerMeters.x + x,
                    hauteurPilier / 2,
                    centerMeters.z + z
                );
                pilier.castShadow = true;
                pilier.receiveShadow = true;
                structureGroup.add(pilier);
            }
        }
        
        console.log(`🏗️ Ombrière: ${nbPiliersDepth * nbPiliersWidth} piliers (espacement ${placeWidth}×${placeDepth}m)`);
        
        // 2. PANNES (poutres horizontales dans le sens de la largeur, tous les placeDepth)
        const panneGeometry = new THREE.BoxGeometry(width, panneWidth, panneWidth);
        
        for (let i = 0; i < nbPiliersDepth; i++) {
            const z = -depth/2 + i * placeDepth;
            const panne = new THREE.Mesh(panneGeometry, metalMaterial);
            panne.position.set(
                centerMeters.x,
                hauteurPilier,
                centerMeters.z + z
            );
            panne.castShadow = true;
            structureGroup.add(panne);
        }
        
        console.log(`🏗️ Ombrière: ${nbPiliersDepth} pannes (section ${panneWidth*100}cm)`);
        
        // 3. FERMES TRIANGULAIRES (entre les pannes, tous les placeDepth)
        for (let i = 0; i < nbPiliersDepth - 1; i++) {
            const z1 = -depth/2 + i * placeDepth;
            const z2 = z1 + placeDepth;
            const zCenter = (z1 + z2) / 2;
            
            // Traverse horizontale haute de la ferme
            const traverseGeometry = new THREE.BoxGeometry(width, fermeWidth, fermeWidth);
            const traverse = new THREE.Mesh(traverseGeometry, metalMaterial);
            traverse.position.set(
                centerMeters.x,
                hauteurPilier + hauteurFerme,
                centerMeters.z + zCenter
            );
            structureGroup.add(traverse);
            
            // Diagonales de la ferme (tous les placeWidth en largeur)
            for (let j = 0; j < nbPiliersWidth - 1; j++) {
                const x1 = -width/2 + j * placeWidth;
                const x2 = x1 + placeWidth;
                const xCenter = (x1 + x2) / 2;
                
                // Diagonale gauche
                const diag1Length = Math.sqrt(Math.pow(placeWidth/2, 2) + Math.pow(hauteurFerme, 2));
                const diag1Geometry = new THREE.BoxGeometry(fermeWidth, fermeWidth, diag1Length);
                const diag1 = new THREE.Mesh(diag1Geometry, metalMaterial);
                const angle1 = Math.atan2(hauteurFerme, placeWidth/2);
                diag1.position.set(
                    centerMeters.x + xCenter - placeWidth/4,
                    hauteurPilier + hauteurFerme/2,
                    centerMeters.z + zCenter
                );
                diag1.rotation.x = Math.PI / 2;
                diag1.rotation.z = -angle1;
                structureGroup.add(diag1);
                
                // Diagonale droite
                const diag2 = diag1.clone();
                diag2.position.x = centerMeters.x + xCenter + placeWidth/4;
                diag2.rotation.z = angle1;
                structureGroup.add(diag2);
            }
        }
        
        console.log(`🏗️ Ombrière: ${nbPiliersDepth - 1} fermes triangulaires (section ${fermeWidth*100}cm, hauteur ${hauteurFerme}m)`);
        
        this.scene.add(structureGroup);
        return structureGroup;
    }
    
    /**
     * Créer un bâtiment 3D à partir des zones de calpinage
     */
    createBuildingFromZones(zones) {
        console.log('🏗️ [3D] createBuildingFromZones appelé avec', zones.length, 'zone(s)');
        
        // Supprimer l'ancien bâtiment s'il existe
        if (this.building3D) {
            this.scene.remove(this.building3D);
        }
        
        // Supprimer les anciennes structures ombrières
        if (this.ombrieres) {
            this.ombrieres.forEach(ombriere => this.scene.remove(ombriere));
        }
        this.ombrieres = [];
        
        if (!zones || zones.length === 0) {
            console.warn('⚠️ [3D] Aucune zone à créer');
            return;
        }
        
        // Séparer ombrières et toitures
        const zonesBatiment = zones.filter(z => z.typeInstallation !== 'ombriere');
        const zonesOmbriere = zones.filter(z => z.typeInstallation === 'ombriere');
        
        // Créer les ombrières
        zonesOmbriere.forEach(zone => {
            console.log(`🅿️ Création ombrière pour zone ${zone.numero}`);
            const ombriereStructure = this.createOmbriereStructure(zone);
            this.ombrieres.push(ombriereStructure);
        });
        
        // Créer le bâtiment pour les autres zones
        if (zonesBatiment.length === 0) {
            console.log('ℹ️ Aucune zone bâtiment (uniquement ombrières)');
            return;
        }
        
        // Groupe pour le bâtiment
        this.building3D = new THREE.Group();
        
        // Calculer le centre moyen des zones bâtiment
        let centerX = 0, centerZ = 0;
        zonesBatiment.forEach(zone => {
            const bounds = zone.layer.getBounds();
            const center = bounds.getCenter();
            centerX += this.latLngToMeters(center.lat, center.lng).x;
            centerZ += this.latLngToMeters(center.lat, center.lng).z;
        });
        centerX /= zonesBatiment.length;
        centerZ /= zonesBatiment.length;
        
        // Créer une toiture pour chaque zone bâtiment
        zonesBatiment.forEach((zone, index) => {
            const bounds = zone.layer.getBounds();
            const sw = bounds.getSouthWest();
            const ne = bounds.getNorthEast();
            
            // Convertir lat/lng en coordonnées métriques
            const swMeters = this.latLngToMeters(sw.lat, sw.lng);
            const neMeters = this.latLngToMeters(ne.lat, ne.lng);
            
            const width = Math.abs(neMeters.x - swMeters.x);
            const depth = Math.abs(neMeters.z - swMeters.z);
            const centerMeters = this.latLngToMeters(
                (sw.lat + ne.lat) / 2,
                (sw.lng + ne.lng) / 2
            );
            
            // Hauteur du bâtiment basée sur le type d'installation
            let height = this.buildingHeight;
            const typeInstallation = document.getElementById('typeInstallation')?.value || 'toiture';
            if (typeInstallation === 'sol') {
                height = 0.5; // Installation au sol (très basse)
            } else if (typeInstallation === 'ombriere') {
                height = 4; // Ombrière de parking
            }
            
            // Créer le toit (simple pour l'instant)
            const inclinaison = zone.inclinaison || 0;
            const orientation = zone.orientation || 180;
            
            // Bâtiment (murs)
            const buildingGeometry = new THREE.BoxGeometry(width, height, depth);
            const buildingMaterial = new THREE.MeshStandardMaterial({
                color: 0x8b7355,
                roughness: 0.8,
                metalness: 0.2
            });
            const buildingMesh = new THREE.Mesh(buildingGeometry, buildingMaterial);
            buildingMesh.position.set(
                centerMeters.x - centerX,
                height / 2,
                centerMeters.z - centerZ
            );
            buildingMesh.castShadow = true;
            buildingMesh.receiveShadow = true;
            this.building3D.add(buildingMesh);
            
            // Toit incliné
            if (inclinaison > 0) {
                const roofGroup = this.createInclinedRoof(width, depth, inclinaison, orientation);
                roofGroup.position.set(
                    centerMeters.x - centerX,
                    height,
                    centerMeters.z - centerZ
                );
                this.building3D.add(roofGroup);
            }
        });
        
        this.scene.add(this.building3D);
        
        // Centrer la caméra sur le bâtiment
        this.camera.lookAt(0, this.buildingHeight / 2, 0);
    }
    
    /**
     * Créer un toit incliné
     */
    createInclinedRoof(width, depth, inclinaisonDegres, orientationDegres) {
        const group = new THREE.Group();
        
        const inclinaisonRad = inclinaisonDegres * Math.PI / 180;
        const hauteurMax = Math.tan(inclinaisonRad) * (depth / 2);
        
        // Géométrie du toit (forme en pente)
        const roofShape = new THREE.Shape();
        roofShape.moveTo(-width/2, 0);
        roofShape.lineTo(width/2, 0);
        roofShape.lineTo(width/2, hauteurMax);
        roofShape.lineTo(-width/2, hauteurMax);
        roofShape.lineTo(-width/2, 0);
        
        const extrudeSettings = {
            steps: 1,
            depth: depth,
            bevelEnabled: false
        };
        
        const roofGeometry = new THREE.ExtrudeGeometry(roofShape, extrudeSettings);
        const roofMaterial = new THREE.MeshStandardMaterial({
            color: 0x8b4513,
            roughness: 0.7,
            metalness: 0.1
        });
        
        const roof = new THREE.Mesh(roofGeometry, roofMaterial);
        roof.rotation.x = -Math.PI / 2;
        roof.position.z = -depth / 2;
        roof.castShadow = true;
        roof.receiveShadow = true;
        
        group.add(roof);
        
        // Rotation selon l'orientation
        group.rotation.y = (orientationDegres - 180) * Math.PI / 180;
        
        return group;
    }
    
    /**
     * Ajouter les modules PV en 3D
     */
    addModules3D(zones) {
        console.log('☀️ [3D] addModules3D appelé avec', zones.length, 'zone(s)');
        
        // Supprimer les anciens modules
        this.modules3D.forEach(module => {
            this.scene.remove(module);
        });
        this.modules3D = [];
        
        if (!zones || zones.length === 0) {
            console.warn('⚠️ [3D] Aucune zone pour modules');
            return;
        }
        
        // Log des zones pour debug
        zones.forEach((zone, i) => {
            console.log(`  Zone ${i}: modulesPositions =`, zone.modulesPositions?.length || 0, 'modules');
        });
        
        // Calculer le centre de référence
        let centerX = 0, centerZ = 0;
        zones.forEach(zone => {
            const bounds = zone.layer.getBounds();
            const center = bounds.getCenter();
            const meters = this.latLngToMeters(center.lat, center.lng);
            centerX += meters.x;
            centerZ += meters.z;
        });
        centerX /= zones.length;
        centerZ /= zones.length;
        
        // Créer les modules pour chaque zone
        zones.forEach(zone => {
            if (!zone.modulesPositions || zone.modulesPositions.length === 0) return;
            
            const moduleLongueurMM = parseFloat(document.getElementById('moduleLongueur')?.value || 2278);
            const moduleLargeurMM = parseFloat(document.getElementById('moduleLargeur')?.value || 1134);
            const moduleOrientation = document.getElementById('moduleOrientation')?.value || 'paysage';
            
            // Dimensions en mètres
            const moduleLongueur = moduleLongueurMM / 1000;
            const moduleLargeur = moduleLargeurMM / 1000;
            
            // Dimensions selon l'orientation
            const moduleWidth = moduleOrientation === 'paysage' ? moduleLongueur : moduleLargeur;
            const moduleDepth = moduleOrientation === 'paysage' ? moduleLargeur : moduleLongueur;
            
            // Géométrie du module (une seule fois pour optimisation)
            const moduleGeometry = new THREE.BoxGeometry(moduleWidth, this.moduleThickness, moduleDepth);
            
            // Matériau des modules PV (bleu plus visible avec émission)
            const moduleMaterial = new THREE.MeshStandardMaterial({
                color: 0x2563eb, // Bleu plus clair et visible
                roughness: 0.2,
                metalness: 0.8,
                emissive: 0x1e40af,
                emissiveIntensity: 0.3 // Plus lumineux pour être visible
            });
            
            // Créer chaque module
            let moduleCount = 0;
            zone.modulesPositions.forEach(modulePos => {
                const meters = this.latLngToMeters(modulePos.lat, modulePos.lng);
                
                const module = new THREE.Mesh(moduleGeometry, moduleMaterial);
                
                // Position du module
                module.position.set(
                    meters.x - centerX,
                    this.buildingHeight + 0.1, // Légèrement au-dessus du toit
                    meters.z - centerZ
                );
                
                // Inclinaison du module
                const inclinaison = zone.inclinaison || 0;
                module.rotation.x = -inclinaison * Math.PI / 180;
                
                // Rotation selon l'orientation du panneau
                const rotationAngle = zone.rotationAngle || 0;
                module.rotation.y = -rotationAngle * Math.PI / 180;
                
                module.castShadow = true;
                module.receiveShadow = true;
                
                this.scene.add(module);
                this.modules3D.push(module);
                moduleCount++;
            });
            
            console.log(`  ✅ Zone ${zones.indexOf(zone)}: ${moduleCount} modules ajoutés`);
        });
        
        console.log(`✅ Total: ${this.modules3D.length} modules PV ajoutés en 3D`);
    }
    
    /**
     * Convertir latitude/longitude en coordonnées métriques (simplifiée)
     */
    latLngToMeters(lat, lng) {
        // Utiliser une projection simple pour la visualisation locale
        // (pour de petites distances, on peut approximer)
        const latRef = prospectLat || 46.5; // Centre France par défaut
        const metersPerDegreeLat = 111320;
        const metersPerDegreeLng = 111320 * Math.cos(latRef * Math.PI / 180);
        
        const x = (lng - (prospectLon || 0)) * metersPerDegreeLng;
        const z = -(lat - (prospectLat || 0)) * metersPerDegreeLat; // Inverser Z
        
        return { x, z };
    }
    
    /**
     * Mettre à jour la position du soleil (heure/saison)
     */
    updateSunPosition(hour = 12, month = 6) {
        if (!this.sunLight) return;
        
        // Simulation simplifiée de la position du soleil
        // Angle horaire (-180° à 180°, midi = 0°)
        const hourAngle = ((hour - 12) / 12) * 180;
        
        // Élévation selon le mois (été = haute, hiver = basse)
        const elevation = 30 + (month - 6) * 5; // 30° à 60°
        
        const distance = 100;
        const elevationRad = elevation * Math.PI / 180;
        const hourAngleRad = hourAngle * Math.PI / 180;
        
        this.sunLight.position.set(
            distance * Math.cos(elevationRad) * Math.sin(hourAngleRad),
            distance * Math.sin(elevationRad),
            distance * Math.cos(elevationRad) * Math.cos(hourAngleRad)
        );
        
        console.log(`☀️ Soleil mis à jour: ${hour}h (mois ${month})`);
    }
    
    /**
     * Boucle d'animation
     */
    animate() {
        if (!this.isActive) return;
        
        requestAnimationFrame(() => this.animate());
        
        // Mettre à jour les contrôles
        if (this.controls) {
            this.controls.update();
        }
        
        // Rendu de la scène
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
    
    /**
     * Gestion du redimensionnement de la fenêtre
     */
    onWindowResize() {
        if (!this.camera || !this.renderer || !this.container) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }
    
    /**
     * Activer/désactiver la vue 3D
     */
    toggle() {
        if (this.isActive) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    /**
     * Afficher la vue 3D
     */
    show() {
        this.container.style.display = 'block';
        if (!this.renderer) {
            this.init();
        }
        this.isActive = true;
        this.animate();
        this.onWindowResize();
    }
    
    /**
     * Masquer la vue 3D
     */
    hide() {
        this.container.style.display = 'none';
        this.isActive = false;
    }
    
    /**
     * Nettoyer les ressources
     */
    dispose() {
        if (this.renderer) {
            this.renderer.dispose();
            this.container.removeChild(this.renderer.domElement);
        }
        this.isActive = false;
    }
}
