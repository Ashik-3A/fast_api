document.addEventListener('DOMContentLoaded', (event) => {
    // Open the default tab on load
    document.querySelector(".sidebar ul li a").click();

    // Load profiles on tab open
    loadProfiles();
});

function openTab(evt, tabName) {
    // Hide all tab contents
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Remove the "active" class from all links
    tablinks = document.querySelectorAll(".sidebar ul li a");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }

    // Show the current tab and add "active" class to the link
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.classList.add("active");

    // Load profiles only when the "Home" tab is opened
    if (tabName === 'home') {
        loadProfiles();
    }

    // Load charts only when the "Dashboard" tab is opened
    if (tabName === 'dashboard') {
        loadCharts();
    }

    // Load cron jobs only when the "Cron Jobs" tab is opened
    if (tabName === 'cron') {
        loadCronJobs();
    }
}

function loadProfiles() {
    fetch('/profiles/')
        .then(response => response.json())
        .then(data => {
                const profilesTable = document.getElementById('profiles-table');
                profilesTable.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Bio</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.profiles.map(profile => `
                            <tr>
                                <td>${profile.id}</td>
                                <td>${profile.username}</td>
                                <td>${profile.email}</td>
                                <td>${profile.bio}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => {
            console.error('Error fetching profiles:', error);
        });
}

function generateUniqueId() {
    return 'id-' + Math.random().toString(36).substr(2, 9); // Example of a random ID generator
}

document.getElementById('create-form').addEventListener('submit', function (event) {
    event.preventDefault();

    const formData = new FormData(this);
    const newProfile = {
        id: generateUniqueId(),
        username: formData.get('username'),
        email: formData.get('email'),
        bio: formData.get('bio')
    };

    fetch('/create_profile/', {
        method: 'POST',
        body: JSON.stringify(newProfile),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        document.getElementById('create-form').reset();
        loadProfiles(); // Refresh profiles after adding a new one
    })
    .catch(error => {
        console.error('Error creating profile:', error);
    });
});

function loadCronJobs() {
    fetch('/cron_jobs/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('cron-jobs-output').textContent = data.cron_jobs;
        })
        .catch(error => {
            console.error('Error loading cron jobs:', error);
            document.getElementById('cron-jobs-output').textContent = 'Error loading cron jobs';
        });
}

document.getElementById('run-cron-job').addEventListener('click', function () {
    fetch('/run_cron_job/', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        })
        .catch(error => {
            console.error('Error running cron job:', error);
        });
});