var webSocket;
var switches;

var log = {
        debug: function(message) {
            if (console && console.debug) {
                console.debug(message)
            }
        },
        info: function(message) {
            if (console && console.info) {
                console.info(message)
            }
        },
        warn: function(message) {
            if (console && console.warn) {
                console.warn(message)
            }
        },
        error: function(message) {
            if (console && console.error) {
                console.error(message)
            }
        }
    };

function openSocket() {
    // Ensures only one connection is open at a time
    if (webSocket !== undefined && webSocket.readyState !== WebSocket.CLOSED) {
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
        if (event.data === undefined)
            return;
    };

    webSocket.onmessage = function(event) {
        try {
            let msg = JSON.parse(event.data);
            switches.updateDevices(msg);
        } catch (e) {
            log.error(e);
        }
    };

    webSocket.onclose = function(event) {
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
        },
    },
    template: '\
        <div class="ctrl-button"> \
            <button v-html="label" v-on:click="sendKey"></button> \
        </div>',
});

// Start

$(function() {
    switches = new Vue({
        el: '#ctrl-switches-container',
        data: {
            visible: false,
            devices: [ ],
        },
        computed: {
        },
        methods: {
            updateDevices: function(message) {
                if ("dev_status" in message) {
                    let devInfo = message.dev_status;
                    let found = false;
                    for (device of this.devices) {
                        if (device.addr == devInfo.logical_address) {
                            device.name = devInfo.osd_name;
                            device.type = devInfo.type;
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        this.devices.push({
                            addr: devInfo.logical_address,
                            name: devInfo.osd_name,
                            type: devInfo.type,
                        })
                        this.devices.sort(function(a,b) {
                            return a.addr - b.addr;
                        })
                    }
                }
            },
            hideSwitches: function() {
                switches.visible = false;
            },
            allOff: function() {
                switches.visible = false;
                data = {
                        allOff: {}
                }
                webSocket.send(JSON.stringify(data));
            },
        }
    });
    
    var ctrlPanel = new Vue({
        el: '.ctrl-panel',
        data: {
        },
        computed: {
        },
        methods: {
            showSwitches: function() {
                switches.visible = true;
            }
        }
    });
    
    openSocket();    
});
