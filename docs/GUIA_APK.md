# 📱 Guía de Compilación APK con Capacitor

## Requisitos Previos

1. **Node.js** >= 18 
2. **Android Studio** con SDK 33+
3. **JDK 17+**

## Pasos

### 1. Instalar dependencias
```bash
cd "c:\Users\teamp\Documents\WORKS UNI I\QUALITY"
npm install
```

### 2. Inicializar Capacitor (solo la primera vez)
```bash
npx cap add android
npx cap sync
```

### 3. Configurar API URL

En `app/app.js`, cambiar `API_BASE` para que apunte a tu servidor:

```js
const API_BASE = 'https://tu-servidor.com/api';
```

### 4. Sincronizar cambios web → Android
```bash
npx cap sync
```

### 5. Abrir en Android Studio
```bash
npx cap open android
```

### 6. Compilar APK debug
```bash
cd android
./gradlew assembleDebug
```

El APK estará en: `android/app/build/outputs/apk/debug/app-debug.apk`

### 7. Compilar APK release (firmado)
```bash
cd android
./gradlew assembleRelease
```

## Notas

- La PWA funciona como app web sin Capacitor en cualquier navegador
- Capacitor envuelve la PWA en un WebView nativo con acceso a APIs del dispositivo
- Las notificaciones push nativas se integran vía `@capacitor/push-notifications`
- El `capacitor.config.json` ya esta preconfigurado con el tema ControlCash
