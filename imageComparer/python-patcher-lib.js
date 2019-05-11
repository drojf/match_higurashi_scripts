'use strict';

let app = null;

// When the main window is loaded
// - Vue components are defined
// - Main Vue instance, called 'app', is initialized
// - the subModHandles are retrieved from the python server to populate the app.subModList property
window.onload = function onWindowLoaded() {
  app = new Vue({
    el: '#app',
    data: {
      leftImage: null,
      rightImage: null,
      currentRow: 0,
    },
    methods: {
      getNext(subModToInstall, installPath) {
        doPost('getNext', { }, (responseData) => {
          console.log(responseData);
          app.leftImage = responseData.leftImage;
          app.rightImage = responseData.rightImage;
          app.currentRow = responseData.currentRow;
        });
      }
    },
    computed: {
    },
  });

};
