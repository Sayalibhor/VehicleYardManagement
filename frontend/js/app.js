const loginForm =
    document.getElementById("loginForm");


if (loginForm) {

    loginForm.addEventListener(
        "submit",
        function(event) {

            event.preventDefault();


            const username =
                document.getElementById(
                    "username"
                ).value;


            const password =
                document.getElementById(
                    "password"
                ).value;


            const message =
                document.getElementById(
                    "message"
                );


            if (
                username === "admin" &&
                password === "1234"
            ) {

                message.innerHTML =
                    "Login successful!";

                message.style.color =
                    "green";


                setTimeout(function() {

                    window.location.href =
                        "pages/dashboard.html";

                }, 500);

            }

            else {

                message.innerHTML =
                    "Invalid username or password.";

                message.style.color =
                    "red";

            }

        }
    );

}