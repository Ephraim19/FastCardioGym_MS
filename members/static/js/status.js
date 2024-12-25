function openTab(evt, tabName) {
            var tabcontents = document.getElementsByClassName("tab-content");
            for (var i = 0; i < tabcontents.length; i++) {
                tabcontents[i].classList.remove("active");
            }
            
            var tablinks = document.getElementsByClassName("tab-button");
            for (var i = 0; i < tablinks.length; i++) {
                tablinks[i].classList.remove("active");
            }
            
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active")
        }