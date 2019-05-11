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
      currentRow: [],
      currentRowIndex: 0, // THIS VALUE IS ZERO INDEXED.
      totalRows: 0,
    },
    methods: {
      getRow(offset) {
        doPost('getNext', { 'offset': offset}, (responseData) => {
          console.log(responseData);
          app.leftImage = responseData.leftImage;
          app.rightImage = responseData.rightImage;
          app.currentRow = responseData.currentRow;
          app.currentRowIndex = responseData.currentRowIndex;
          app.totalRows = responseData.totalRows;
        });
      }
    },
    computed: {
    },
  });

  //restore state of the gui with the current row
  app.getRow(0);

};
