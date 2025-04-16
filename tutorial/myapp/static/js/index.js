import { ApollonEditor } from './node_modules/@ls1intum/apollon/lib/es6/index.js';


  document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('apollon-container');
    const editor = new ApollonEditor(container, {
      mode: 'ClassDiagram',
      locale: 'de',
    });

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('json_file');
    const uploadForm = document.getElementById('uploadForm');

    // Prevent navigating away on dragover
    dropZone.addEventListener('dragover', function(e) {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
    });

    // Handle the dropped file
    dropZone.addEventListener('drop', function(e) {
      e.preventDefault();
      fileInput.files = e.dataTransfer.files;
      uploadForm.submit();
    });

    // Example: Export diagram as JSON
    document.getElementById('export-button').addEventListener('click', () => {
      const diagram = editor.model;
      console.log(JSON.stringify(diagram));
    });
  });