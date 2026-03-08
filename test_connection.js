const axios = require('axios');

async function debugConnect() {
    const url = 'http://127.0.0.1:5001/';
    console.log(`Checking connection to: ${url}`);
    try {
        const response = await axios.get(url);
        console.log('Success:', response.status, response.data);
    } catch (error) {
        console.error('Error:', error.message);
        if (error.response) {
            console.error('Response data:', error.response.data);
        }
    }
}

debugConnect();
