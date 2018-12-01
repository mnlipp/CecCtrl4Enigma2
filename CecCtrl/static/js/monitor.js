var webSocket;
var messages = $("#messages");

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

/**
 * Sends the value of the text input to the server
 */
function send(target, data) {
    var msg = target + "<" + data
    webSocket.send(msg);
}

function closeSocket() {
    webSocket.close();
}

function writeResponse(text) {
    messages.append("<br/>");
    var line = $("<span></span>");
    line.text(text);
    messages.append(line);
    window.scrollTo(0, document.body.scrollHeight);
}

// Command dialog

function checkPhysicalAddress(text) {
    let pattern = /^(\d{1,2}):(\d{1,2}):(\d{1,2}):(\d{1,2})$/;
    return text.match(pattern);
}

Vue.component("cec-argument", {
    props: {
        commandString: {
            type: String,
            required: true,
        },
        remainingArgumentTypes: {
            type: Array,
            required: true,
        }
    },
    data: function() {
        return {};
    },
    computed: {
        currentType: function() {
            if (this.remainingArgumentTypes.length == 0) {
                return "";
            }
            return this.remainingArgumentTypes[0];
        },
        broadcastOnly: function() {
            return this.$parent.broadcastOnly;
        },
    },
    template: "#cecArgumentInput",
});

Vue.component("cec-physical-input", {
    props: {
        commandString: {
            type: String,
            required: true,
        },
        remainingArgumentTypes: {
            type: Array,
            required: true,
        }
    },
    data: function() {
        return {
            address: "",
        };
    },
    computed: {
        parsedAddress: function() {
            let match = checkPhysicalAddress(this.address);
            if (match == null) {
                return null;
            }
            return (parseInt(match[1], 0x10) * 16 + parseInt(match[2], 0x10)).toString(16) +
                ":" + (parseInt(match[3], 0x10) * 16 + parseInt(match[4], 0x10)).toString(16);
        },
        broadcastOnly: function() {
            return this.$parent.broadcastOnly;
        },
    },
    methods: {
        appendAddress: function(current) {
            if (this.parsedAddress) {
                return current + ":" + this.parsedAddress;
            }
            return current;
        }
    },
    template: '\
        <span> \
          <input v-model="address" class="physicalAddress erroneous" type="text"/> \
          <cec-argument \
              v-bind:command-string="appendAddress(commandString)" \
              v-bind:remaining-argument-types="remainingArgumentTypes.slice(1)"></cec-argument> \
        </span>',
});

Vue.component("cec-abort-reason-input", {
    props: {
        commandString: {
            type: String,
            required: true,
        },
        remainingArgumentTypes: {
            type: Array,
            required: true,
        }
    },
    data: function() {
        return {
            reasonAsString: "0",
            abortReason: cecMonitor.abortReason,
        };
    },
    computed: {
        broadcastOnly: function() {
            return this.$parent.broadcastOnly;
        },
    },
    methods: {
        appendReason: function(current) {
            return current + ":" + this.reasonAsString;
        }
    },
    template: '\
        <span> \
          <select v-model="reasonAsString"> \
            <option v-for="selectValue in Object.keys(abortReason)" v-bind:value="selectValue.toString(0x10)">{{ abortReason[selectValue] }}</option> \
          </select> \
          <cec-argument \
              v-bind:command-string="appendReason(commandString)" \
              v-bind:remaining-argument-types="remainingArgumentTypes.slice(1)"></cec-argument> \
        </span>',
});

Vue.component("cec-power-status-input", {
    props: {
        commandString: {
            type: String,
            required: true,
        },
        remainingArgumentTypes: {
            type: Array,
            required: true,
        }
    },
    data: function() {
        return {
            statusAsString: "0",
            powerStatus: cecMonitor.powerStatus,
        };
    },
    computed: {
        broadcastOnly: function() {
            return this.$parent.broadcastOnly;
        },
    },
    methods: {
        appendStatus: function(current) {
            return current + ":" + this.statusAsString;
        }
    },
    template: '\
        <span> \
          <select v-model="statusAsString"> \
            <option v-for="selectValue in Object.keys(powerStatus)" v-bind:value="selectValue.toString(0x10)">{{ powerStatus[selectValue] }}</option> \
          </select> \
          <cec-argument \
              v-bind:command-string="appendStatus(commandString)" \
              v-bind:remaining-argument-types="remainingArgumentTypes.slice(1)"></cec-argument> \
        </span>',
});

Vue.component("cec-device-type-input", {
    props: {
        commandString: {
            type: String,
            required: true,
        },
        remainingArgumentTypes: {
            type: Array,
            required: true,
        }
    },
    data: function() {
        return {
            deviceAsString: "0",
            deviceType: cecMonitor.deviceType,
        };
    },
    computed: {
        broadcastOnly: function() {
            return this.$parent.broadcastOnly;
        },
    },
    methods: {
        appendDevice: function(current) {
            return current + ":" + this.deviceAsString;
        }
    },
    template: '\
        <span> \
          <select v-model="deviceAsString"> \
            <option v-for="selectValue in Object.keys(deviceType)" v-bind:value="selectValue.toString(0x10)">{{ deviceType[selectValue] }}</option> \
          </select> \
          <cec-argument \
              v-bind:command-string="appendDevice(commandString)" \
              v-bind:remaining-argument-types="remainingArgumentTypes.slice(1)"></cec-argument> \
        </span>',
});

Vue.component("cec-user-control-code-input", {
    props: {
        commandString: {
            type: String,
            required: true,
        },
        remainingArgumentTypes: {
            type: Array,
            required: true,
        }
    },
    data: function() {
        return {
            uccAsString: "0",
            userControlCode: cecMonitor.userControlCode,
        };
    },
    computed: {
        broadcastOnly: function() {
            return this.$parent.broadcastOnly;
        },
    },
    methods: {
        appendUcc: function(current) {
            return current + ":" + this.uccAsString;
        }
    },
    template: '\
        <span> \
          <select v-model="uccAsString"> \
            <option v-for="selectValue in Object.keys(userControlCode)" v-bind:value="selectValue.toString(0x10)">{{ userControlCode[selectValue] }}</option> \
          </select> \
          <cec-argument \
              v-bind:command-string="appendUcc(commandString)" \
              v-bind:remaining-argument-types="remainingArgumentTypes.slice(1)"></cec-argument> \
        </span>',
});

Vue.component("cec-opaque-input", {
    props: {
        commandString: {
            type: String,
            required: true,
        },
        remainingArgumentTypes: {
            type: Array,
            required: true,
        }
    },
    data: function() {
        return {
            args: "",
        };
    },
    computed: {
        broadcastOnly: function() {
            return this.$parent.broadcastOnly;
        },
    },
    methods: {
        appendArgs: function(current) {
            return current + ":" + this.args;
        }
    },
    template: '\
        <span> \
          <input v-model="args" class="opaqueData" type="text"/> \
          <cec-final-input \
              v-bind:command-string="appendArgs(commandString)"></cec-final-Input> \
        </span>',
});

Vue.component("cec-final-input", {
    props: {
        commandString: {
            type: String,
            required: true,
        },
    },
    data: function() {
        return {
            target: "",
        };
    },
    computed: {
        broadcastOnly: function() {
            return this.$parent.broadcastOnly;
        },
        targetAddress: function() {
            if (this.broadcastOnly) {
                return "15";
            }
            return this.target;
        }
    },
    methods: {
        submit: function() {
            send(this.targetAddress, this.commandString);
        }
    },
    template: '\
        <span> \
          to <span v-if="broadcastOnly">15</span> \
          <input v-else v-model="target" class="targetAddress" type="text" /> \
          <button type="button" v-on:click="submit()">Send</button> \
        </span>',
});

var commandDialog = new Vue({
    el: '#inputPanel',
    data: {
        commandCodeAsString: "FF",
    },
    computed: {
        commandCode: function() {
            return parseInt(this.commandCodeAsString, 0x10);
        },
        commandName: function() {
            return cecMonitor.cecCommands[this.commandCode][0];
        },
        commandFlags: function() {
            return cecMonitor.cecCommands[this.commandCode][1].split('');
        },
        broadcastOnly: function() {
            return this.commandFlags.includes("B");
        },        
    }
  });

$("#inputPanel").on('input propertychange', '.physicalAddress', function() {
    var $this = $(this);
    var newValue = $this.val();
    
    if (checkPhysicalAddress(newValue) != null) {
        $this.removeClass("erroneous");
    } else {
        $this.addClass("erroneous");
    }
    return $this.data('oldValue',newValue)
});


// Start

$(openSocket);
