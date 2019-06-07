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
      alreadyMatched: false,
      jumpIndex: 1,
    },
    methods: {
      getBase(responseData) {
        if(responseData === null)
        {
          alert("no row found for your query!");
        }

        console.log(responseData);
        app.leftImage = responseData.leftImage;
        app.rightImage = responseData.rightImage;
        app.currentRow = responseData.currentRow;
        app.currentRowIndex = responseData.currentRowIndex;
        app.totalRows = responseData.totalRows;
        app.alreadyMatched = responseData.alreadyMatched;
      },
      getNextUnsaved() {
        doPost('getNextUnsaved', { }, (responseData) => { app.getBase(responseData); });
      },
      getRowAbsolute(index) {
        doPost('getRowAbsolute', { 'index': index-1}, (responseData) => { app.getBase(responseData); });
      },
      getRow(offset) {
        doPost('getNext', { 'offset': offset}, (responseData) => { app.getBase(responseData); });
      },
      saveMapping() {
        doPost('saveMapping', { 'leftImage': app.leftImage, 'rightImage': app.rightImage}, (responseData) => {
          console.log(responseData);
          app.getRow(0);
        });
      },
    },
    computed: {
    },
  });

  //restore state of the gui with the current row
  app.getRow(0);

};
