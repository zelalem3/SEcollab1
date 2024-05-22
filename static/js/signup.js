document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('form').addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent form submission

        // Get the form element
        var form = document.querySelector('form');

        // Get the username input value
        var username = document.getElementById("username").value;

        // Check if the username is already taken
        fetch("http://127.0.0.1:5000/fetchusername/" + username, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        })
        .then(response => {
            if (response.ok) {
                // If the username is available, submit the form
                form.submit();
            } else {
                // If the username is not available, display an error message
                var usernameText = document.getElementById("usernametext");
                usernameText.textContent = "Username is already taken";
                throw new Error("Username is already taken");
            }
        })
        .catch(error => {
            console.error(error);
        });
    });
});
