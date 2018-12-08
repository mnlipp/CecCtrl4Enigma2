var webSocket;

function openSocket() {
    // Ensures only one connection is open at a time
    if (webSocket !== undefined && webSocket.readyState !== WebSocket.CLOSED) {
        writeResponse("WebSocket is already opened.");
        return;
    }
    // Create a new instance of the websocket
    var loc = window.location, new_uri;
    if (loc.protocol === "https:") {
        new_uri = "wss:";
    } else {
        new_uri = "ws:";
    }
    new_uri += "//" + loc.host;
    new_uri += loc.pathname + "/socket";
    webSocket = new WebSocket(new_uri);

    /**
     * Binds functions to the listeners for the websocket.
     */
    webSocket.onopen = function(event) {
        // For reasons I can't determine, onopen gets called twice
        // and the first time event.data is undefined.
        // Leave a comment if you know the answer.
        writeResponse("Monitor started.");
        if (event.data === undefined)
            return;

        writeResponse(event.data);
    };

    webSocket.onmessage = function(event) {
        writeResponse(event.data);
    };

    webSocket.onclose = function(event) {
        writeResponse("Connection closed");
    };
}

function closeSocket() {
    webSocket.close();
}

// Components

Vue.component("cec-remote-button", {
    props: {
        label: {
            type: String,
            required: true,
        },
        code: {
            type: Number,
            required: true,
        }
    },
    data: function() {
        return {
        };
    },
    computed: {
    },
    methods: {
        sendKey: function() {
            data = {
                    key: {
                        code: this.code,
                    }
            }
            webSocket.send(JSON.stringify(data));
        }
    },
    template: '\
        <div class="ctrl-button"> \
            <button v-html="label" v-on:click="sendKey"></button> \
        </div>',
});


// Start

$(function() {
    var ctrlPanel = new Vue({
        el: '.ctrl-panel',
        data: {
        },
        computed: {
        }
    });
    
    openSocket();    
});
