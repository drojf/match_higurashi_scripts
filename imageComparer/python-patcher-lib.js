'use strict';

let app = null;

// This variable caches html elements - it is initalized in the window.onload callback
let el = {};
let numberOfBlankLinesInARow = 0;

// This is a handle to the setWindow(statusUpdate()) timer
let statusUpdateTimerHandle = null;

// Step 4.
// Attempts to start the install to the given installPath.
// If the installPath argument is not given, then the python
// server will open a file chooser GUI to choose the path.
// If the install starts successfully, a interval timer wil call
// the statusUpdate() function every 1s. Otherwise, the user is notified
// that the install failed to start.
function startInstall(subModToInstall, installPath) {
  if (app.installStarted) {
    alert("Installer is already running!");
    return;
  }

  doPost('startInstall',
    { subMod: subModToInstall, installPath },
    (responseData) => {
      console.log(responseData);
      if (responseData.installStarted) {
        statusUpdateTimerHandle = window.setInterval(statusUpdate, 500);
        app.installStarted = true;
        window.scrollTo(0, 0);
      } else {
        alert('The install could not be started. Reason: {INSERT REASON HERE}. Please ensure you chose a valid path.');
      }
    });
}

// When the main window is loaded
// - Vue components are defined
// - Main Vue instance, called 'app', is initialized
// - the subModHandles are retrieved from the python server to populate the app.subModList property
window.onload = function onWindowLoaded() {
  app = new Vue({
    el: '#app',
    data: {
      subModList: [], // populated in at the end of this function (onWindowLoaded())
      selectedMod: null, // changes when user chooses a [mod] by pressing a vue-mod-button
      selectedSubMod: null, // changes when user chooses a [subMod] by pression a vue-submod-button
      fullInstallConfigs: [], // updates when when a [selectedSubMod] is changes, cleared when [selectedMod] changes
      installStarted: false,
      installFinished: false,
      installFailed: false,
      showTroubleshooting: false,
      overallPercentage: 0,
      subTaskPercentage: 0,
      overallTaskDescription: 'Overall Task Description',
      subTaskDescription: 'Sub Task Description',
      selectedInstallPath: null, // After an install successfully started, this contains the install path chosen
      validatedInstallPath: null,
      installPathValid: false,
      validationInProgress: true,
      installPathFocussed: false,
      logFilePath: null, // When window loaded, this script queries the installer as to the log file path
      os: null, // the host operating system detected by the python script - either 'windows', 'linux', or 'mac'
    },
    methods: {
      doInstall() {
        console.log(`Trying to start install to ${app.selectedInstallPath} Submod:`);
        console.log(app.selectedSubMod);
        startInstall(app.selectedSubMod, app.selectedInstallPath);
      },
      onChoosePathButtonClicked(pathToInstall) {
        if (pathToInstall === undefined) {
          doPost('showFileChooser', app.selectedSubMod.id, (responseData) => {
            if (responseData.path === null) {
              alert("You didn't select a path!");
            } else {
              app.selectedInstallPath = responseData.path;
            }
          });
        } else {
          app.selectedInstallPath = pathToInstall;
        }
      },
      // If argument 'installPath' is null, then a file chooser will let user choose game path
      getLogsZip(subModToInstall, installPath) {
        doPost('troubleshoot', { action: 'getLogsZip', subMod: subModToInstall, installPath }, (responseData) => {
          console.log(responseData);
          window.location.href = responseData.filePath;
        });
      },
      openSaveFolder(subModToInstall, installPath) {
        doPost('troubleshoot', { action: 'openSaveFolder', subMod: subModToInstall, installPath }, () => {});
      },
      renderMarkdown(markdownText) {
        return marked(markdownText, { sanitize: true });
      },
      validateInstallPath() {
        // Just validate the install - don't actually start the installation
        doPost('startInstall', { subMod: app.selectedSubMod, installPath: app.selectedInstallPath, validateOnly: true },
          (responseData) => {
            app.installPathValid = responseData.installStarted;
            app.validatedInstallPath = responseData.validatedInstallPath;
            app.validationInProgress = false;
          });
      },
    },
    computed: {
      modHandles() {
        const modHandlesList = [];
        const uniqueMods = new Set();

        this.subModList.forEach((subModHandle) => {
          if (!uniqueMods.has(subModHandle.modName)) {
            modHandlesList.push({ modName: subModHandle.modName, key: subModHandle.id });
            uniqueMods.add(subModHandle.modName);
          }
        });

        return modHandlesList;
      },
      possibleSubMods() {
        return this.subModList.filter(x => x.modName === this.selectedMod);
      },
    },
    watch: {
      // This sets the app.selectedSubMod to the first subMod in the subModList.
      // However it is disabled for now, so the default value is 'null'.
      // When the app.selectedSubMod is 'null', the "Intro/Troubleshooting" page is displayed.
      selectedMod: function onselectedMod(newselectedMod, oldSelectedMod) {
        this.selectedSubMod = this.possibleSubMods[0];
      },
      selectedSubMod: function onSelectedSubModChanged(newSelectedSubMod, oldSelectedSubMod) {
        if (newSelectedSubMod !== null) {
          doPost('gamePaths', { id: newSelectedSubMod.id }, (responseData) => { console.log(responseData); this.fullInstallConfigs = responseData; });
        } else {
          this.fullInstallConfigs = [];
        }
      },
      selectedInstallPath: function onSelectedInstallPathChanged(newPath, oldPath) {
        if (newPath !== null) {
          app.validationInProgress = true;
          app.showConfirmation = true;
          if (app.installPathFocussed) {
            app.debouncedValidateInstallPath();
          } else {
            app.validateInstallPath();
          }
        }
      },
    },
  });

  el = {
    terminal: document.getElementById('terminal'),
  };

};
