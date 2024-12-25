document.querySelector('.download-btn').addEventListener('click', function() {
    console.log('Download button clicked');

    // Perform a GET request to the Django path to get the download URL
    fetch('/reports/download/?start_date=2024-01-01&end_date=2024-11-24', {
        method: 'GET', // Specify the HTTP method
    })
    .then(response => response.json())
    .then(data => {
        const downloadUrl = data.download_url;
        console.log('Download URL:', downloadUrl);
        // Create a link to download the file
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = downloadUrl.split('/').pop(); // Extract filename from URL
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        console.log('File download started');
    })
    .catch(error => {
        console.error('There was an error!', error);
    });
});
