# Cards

The 205 launch cards of the Visual Programming Project, grouped into 8 categories. Each card has one clear name, one category and one sentence on what it will do. This file names and describes cards only. Ports, settings, Python templates and tests come in a later phase.

- Card numbers run in order through this file. They are working numbers and change when cards are added or removed; the blank catalog in `prototype/catalog.js` still holds the older 200-card layout.
- Each card sits in exactly one category. The "Group" column is a sub-theme inside the category.
- The framework names 200 cards as a target, not a fixed limit. Cards were added and removed after independent review.
- Rules from the framework that shape these cards: the app runs locally for one owner on test data; connectors never call outside services; AI cards help at build time or take an answer a person brings in; triggers run only while the preview runs; loops live inside one card and are bounded.

## Categories

| Category | Cards | Numbers | What the cards share |
| --- | --- | --- | --- |
| UI / Interface | 34 | 001-034 | Cards the person using the app sees and touches: inputs, controls, layouts and displays. |
| Backend Processing | 64 | 035-098 | Cards that work on data while it moves through a flow, with no screen of their own. |
| Data Modeling / Storage | 33 | 099-131 | Cards that define the shape of records and read or write the app's saved data. |
| Logic / Validation | 22 | 132-153 | Cards that decide whether data or an action is acceptable, and which rule applies. |
| Triggers / Orchestration | 14 | 154-167 | Cards that start a flow or set the order in which steps run, only while the local preview runs. |
| Integrations / Connectors | 20 | 168-187 | Cards that prepare work for a person to do outside the app and take the result back; the app itself makes no outside call. |
| AI Capabilities | 10 | 188-197 | Cards where AI helps build the app or a person brings in an AI answer; the running app never calls AI. |
| Navigation / Output | 8 | 198-205 | Cards that move the user between screens and present or hand over final results. |
| **Total** | **205** | 001-205 | |

## UI / Interface (34 cards)

Cards the person using the app sees and touches: inputs, controls, layouts and displays.

| No. | Name | Category | Group | What it does |
| --- | --- | --- | --- | --- |
| 001 | Enter Text | UI / Interface | Form Inputs | Lets the user type a single line of text into a labeled field. |
| 002 | Enter Paragraph | UI / Interface | Form Inputs | Lets the user type multiple lines of text into a labeled box. |
| 003 | Enter Number | UI / Interface | Form Inputs | Lets the user type or adjust a numeric value with optional min and max. |
| 004 | Pick Date | UI / Interface | Form Inputs | Lets the user select a date from a calendar popup. |
| 005 | Pick Time | UI / Interface | Form Inputs | Lets the user select a time of day from hour and minute controls. |
| 006 | Enter Email Address | UI / Interface | Form Inputs | Lets the user type an email address into a validated field. |
| 007 | Enter Phone Number | UI / Interface | Form Inputs | Lets the user type a phone number into a formatted field. |
| 008 | Enter Currency Amount | UI / Interface | Form Inputs | Lets the user type a monetary value with currency symbol and formatting. |
| 009 | Pick Date Range | UI / Interface | Form Inputs | Lets the user choose a start date and an end date together from one calendar. |
| 010 | Choose From Dropdown | UI / Interface | Selection Controls | Lets the user pick one option from a collapsible list. |
| 011 | Select Multiple Options | UI / Interface | Selection Controls | Lets the user check multiple items from a displayed list. |
| 012 | Choose One Option | UI / Interface | Selection Controls | Lets the user select exactly one choice from visible radio buttons. |
| 013 | Toggle Checkbox | UI / Interface | Selection Controls | Lets the user check or uncheck a single yes or no option. |
| 014 | Pick From Searchable List | UI / Interface | Selection Controls | Lets the user type to narrow a long list and pick one entry. |
| 015 | Rate With Stars | UI / Interface | Selection Controls | Lets the user choose a rating by clicking one to five stars. |
| 016 | Arrange In Grid | UI / Interface | Layout Containers | Displays child cards in rows and columns with equal spacing. |
| 017 | Stack In Panel | UI / Interface | Layout Containers | Groups child cards vertically in a bordered section with optional title. |
| 018 | Organize In Tabs | UI / Interface | Layout Containers | Shows one group of cards at a time under clickable tab labels. |
| 019 | Split Into Columns | UI / Interface | Layout Containers | Divides the space into side by side sections for child cards. |
| 020 | Collapse Section | UI / Interface | Layout Containers | Hides or shows child cards when the user clicks the section header. |
| 021 | Set App Title | UI / Interface | Layout Containers | Sets the name shown at the top of the app and in the window title. |
| 022 | Show Records Table | UI / Interface | Data Display | Displays rows of data in sortable columns with optional pagination. |
| 023 | List Records | UI / Interface | Data Display | Shows data items one per row with icon and text summary. |
| 024 | Display Record Card | UI / Interface | Data Display | Presents a single record's fields in labeled rows or compact layout. |
| 025 | Show Detail View | UI / Interface | Data Display | Displays all fields of one selected record in organized sections. |
| 026 | Show Status Badge | UI / Interface | Data Display | Displays a colored label indicating state like pending approved or shipped. |
| 027 | Display Barcode From Code | UI / Interface | Data Display | Shows a barcode image created from the product code or identifier of a record. |
| 028 | Click Button | UI / Interface | Interactive Controls | Triggers an action when the user clicks the labeled button. |
| 029 | Switch Toggle | UI / Interface | Interactive Controls | Lets the user turn a setting on or off with a sliding switch. |
| 030 | Adjust Slider | UI / Interface | Interactive Controls | Lets the user pick a value by dragging a handle along a range. |
| 031 | Choose File | UI / Interface | Interactive Controls | Lets the user browse and select a local file for upload or reading. |
| 032 | Confirm Action | UI / Interface | Interactive Controls | Asks the user to approve or cancel before proceeding with an action. |
| 033 | Show Message Banner | UI / Interface | Interactive Controls | Displays a dismissible notice with success warning or error styling. |
| 034 | Show Progress While Running | UI / Interface | Interactive Controls | Displays a progress bar or spinner during a long running step like importing data. |

## Backend Processing (64 cards)

Cards that work on data while it moves through a flow, with no screen of their own.

| No. | Name | Category | Group | What it does |
| --- | --- | --- | --- | --- |
| 035 | Convert Field Type | Backend Processing | Field Transformations | Changes a field from one data type to another, such as text to number or date to text. |
| 036 | Format Currency Value | Backend Processing | Field Transformations | Displays a number as currency with symbol, decimal places, and thousands separator. |
| 037 | Extract Substring | Backend Processing | Field Transformations | Pulls out a portion of text from a field using start position and length. |
| 038 | Combine Multiple Fields | Backend Processing | Field Transformations | Joins two or more fields into one with optional separator text between them. |
| 039 | Round Numeric Value | Backend Processing | Field Transformations | Rounds a number to a specified number of decimal places or to the nearest whole number. |
| 040 | Trim Whitespace | Backend Processing | Field Transformations | Removes leading and trailing spaces or line breaks from a text field. |
| 041 | Change Text Case | Backend Processing | Field Transformations | Converts text to uppercase, lowercase, or title case as specified. |
| 042 | Generate Unique Identifier | Backend Processing | Field Transformations | Creates a unique code for each new record from a prefix and a counter saved with the table. |
| 043 | Extract Domain From Email | Backend Processing | Field Transformations | Pulls the domain portion from an email address field for grouping or filtering. |
| 044 | Format Phone Number | Backend Processing | Field Transformations | Standardizes phone numbers to a consistent display format with area code and separators. |
| 045 | Filter Records By Condition | Backend Processing | List Operations | Keeps only the records in the current list that meet one or more conditions and drops the rest. |
| 046 | Sort Records By Field | Backend Processing | List Operations | Arranges the records in the current list in ascending or descending order of one or more fields. |
| 047 | Group Records By Value | Backend Processing | List Operations | Organizes records into named groups based on a shared field value or category. |
| 048 | Remove Duplicate Records | Backend Processing | List Operations | Identifies and removes records with matching values in specified fields from the list. |
| 049 | Paginate Record List | Backend Processing | List Operations | Splits a list into fixed-size pages and returns one page at a time. |
| 050 | Take Record Range | Backend Processing | List Operations | Returns part of a list of records, from a start position to an end position. |
| 051 | Find First Matching Record | Backend Processing | List Operations | Searches a list and returns the first record that meets the specified condition. |
| 052 | Flag Unusual Records | Backend Processing | List Operations | Marks records whose value falls outside a normal range the builder sets, such as far above the average. |
| 053 | Merge Two Lists | Backend Processing | List Operations | Combines two lists of records into one list, optionally dropping repeated records. |
| 054 | Calculate Sum Of Field | Backend Processing | Calculations | Adds up numeric values from a specified field across all records in a list. |
| 055 | Calculate Average Value | Backend Processing | Calculations | Computes the mean of numeric values from a field across a set of records. |
| 056 | Calculate Percentage Of Total | Backend Processing | Calculations | Divides a value by a sum and expresses the result as a percentage. |
| 057 | Find Minimum Value | Backend Processing | Calculations | Identifies the smallest numeric value in a field across a list of records. |
| 058 | Find Maximum Value | Backend Processing | Calculations | Identifies the largest numeric value in a field across a list of records. |
| 059 | Calculate Running Total | Backend Processing | Calculations | Adds each value to the sum of all previous values in sequence. |
| 060 | Calculate Stock Level | Backend Processing | Calculations | Computes current inventory by subtracting outgoing quantity from incoming quantity and starting balance. |
| 061 | Count Records Matching Condition | Backend Processing | Calculations | Counts the records in the current list, or only those that meet a condition. |
| 062 | Calculate Reorder Quantity | Backend Processing | Calculations | Works out the next order amount from past usage with a plain formula, such as average use times lead time. |
| 063 | Calculate From Two Values | Backend Processing | Calculations | Adds, subtracts, multiplies or divides two numbers, such as stock counted minus stock on record. |
| 064 | Change Value By Percent | Backend Processing | Calculations | Raises or lowers an amount by a percentage, for example to add tax or take off a discount. |
| 065 | Calculate Percentage Change | Backend Processing | Calculations | Shows how much a value rose or fell compared with an earlier value, as a percentage. |
| 066 | Split Text By Separator | Backend Processing | Text Processing | Splits text into separate values wherever a separator such as a comma, tab or vertical bar appears. |
| 067 | Search Text For Pattern | Backend Processing | Text Processing | Finds whether a text field contains a specified word, phrase, or pattern. |
| 068 | Replace Text In Field | Backend Processing | Text Processing | Substitutes all occurrences of specified text with replacement text in a field. |
| 069 | Split Text Into Lines | Backend Processing | Text Processing | Breaks multi-line text into separate strings, one per line, for individual processing. |
| 070 | Fill Text Template | Backend Processing | Text Processing | Inserts field values into a template with placeholders to generate formatted text output. |
| 071 | Extract Number From Text | Backend Processing | Text Processing | Finds the first whole or decimal number in a text field and ignores the other characters. |
| 072 | Remove Special Characters | Backend Processing | Text Processing | Strips out non-alphanumeric characters from text, keeping only letters, numbers, and spaces. |
| 073 | Label Text By Keywords | Backend Processing | Text Processing | Gives each text record a label by matching keywords from a list the builder sets. |
| 074 | Calculate Date Difference | Backend Processing | Date and Time Operations | Computes the number of days, hours, or minutes between two dates or timestamps. |
| 075 | Add Time To Date | Backend Processing | Date and Time Operations | Advances a date forward by a specified number of days, hours, or minutes. |
| 076 | Subtract Time From Date | Backend Processing | Date and Time Operations | Moves a date backward by a specified number of days, hours, or minutes. |
| 077 | Compare Two Dates | Backend Processing | Date and Time Operations | Determines whether one date is before, after, or equal to another date. |
| 078 | Calculate Working Days | Backend Processing | Date and Time Operations | Counts weekdays between two dates, excluding weekends and optionally holidays. |
| 079 | Get Current Date And Time | Backend Processing | Date and Time Operations | Returns the present date and time when the card executes during preview. |
| 080 | Merge Two Records | Backend Processing | Record Assembly | Combines fields from two records into one, with options for handling duplicate field names. |
| 081 | Build Record From Fields | Backend Processing | Record Assembly | Creates a new record by selecting and assembling individual field values. |
| 082 | Rename Record Fields | Backend Processing | Record Assembly | Changes field names in a record to new names while keeping values unchanged. |
| 083 | Keep Only Selected Fields | Backend Processing | Record Assembly | Keeps only the named fields of a record and drops all the others. |
| 084 | Join Records Into List | Backend Processing | Record Assembly | Collects multiple individual records into a single list for batch processing. |
| 085 | Route By Status Value | Backend Processing | Conditional Routing | Sends a record to the output for its status value; records with any other status go to a no-match output. |
| 086 | Route By Numeric Range | Backend Processing | Conditional Routing | Sends a record to the output whose number range it falls in; records outside every range go to a no-match output. |
| 087 | Route By Text Match | Backend Processing | Conditional Routing | Sends a record to an output when a text field matches a chosen value; other records go to a no-match output. |
| 088 | Route By Field Presence | Backend Processing | Conditional Routing | Sends a record one way if a field has a value and another way if it is empty. |
| 089 | Route By Date Comparison | Backend Processing | Conditional Routing | Sends a record to an output depending on whether a date is in the past, today or in the future. |
| 090 | Route By Category | Backend Processing | Conditional Routing | Sends a record to the output for its category or type; records with an unlisted category go to a no-match output. |
| 091 | Route By List Membership | Backend Processing | Conditional Routing | Sends a record one way if a field value appears in a reference list and another way if it does not. |
| 092 | Handle Error Without Stopping | Backend Processing | Error Handling | Catches a failure in a step so the rest of the flow can carry on along an error path. |
| 093 | Set Default Value On Error | Backend Processing | Error Handling | Provides a fallback value when a field calculation or transformation fails. |
| 094 | Retry Failed Step | Backend Processing | Error Handling | Runs a failed local step again a set number of times, only if it is safe to repeat, then follows the error path. |
| 095 | Log Error Details | Backend Processing | Error Handling | Records information about a failure for review without stopping the application flow. |
| 096 | Flag Record With Error | Backend Processing | Error Handling | Marks a record as having encountered a problem and continues processing remaining records. |
| 097 | Skip Invalid Record | Backend Processing | Error Handling | Removes a record from further processing when it fails validation or transformation. |
| 098 | Collect Error Records | Backend Processing | Error Handling | Gathers all records that encountered errors into a separate list for review. |

## Data Modeling / Storage (33 cards)

Cards that define the shape of records and read or write the app's saved data.

| No. | Name | Category | Group | What it does |
| --- | --- | --- | --- | --- |
| 099 | Define Data Table | Data Modeling / Storage | Schema Definition | Creates a new table with a name and description to hold records in the app. |
| 100 | Add Field To Table | Data Modeling / Storage | Schema Definition | Adds a named column to a table with a data type, and optional simple rules such as required or a number range. |
| 101 | Set Field Default Value | Data Modeling / Storage | Schema Definition | Assigns a default value that fills automatically when creating a new record in the table. |
| 102 | Link Tables By Relationship | Data Modeling / Storage | Schema Definition | Connects two tables so records in one can reference records in the other. |
| 103 | Define Choice List | Data Modeling / Storage | Schema Definition | Creates a dropdown list of allowed values that a field can use across the app. |
| 104 | Add Calculated Field | Data Modeling / Storage | Schema Definition | Defines a field whose value is worked out from other fields in the same record, using a formula the builder sets. |
| 105 | Enable Change History Tracking | Data Modeling / Storage | Schema Definition | Makes a table keep the last few versions of each record, with when each change was made. |
| 106 | Define App Settings | Data Modeling / Storage | Schema Definition | Keeps the owner's app-wide options, such as default currency or reorder level, in one saved settings record. |
| 107 | Create New Record | Data Modeling / Storage | Record Operations | Adds a single record to a table with values the user provides or maps from inputs. |
| 108 | Read Record By ID | Data Modeling / Storage | Record Operations | Retrieves one record from a table using its unique identifier. |
| 109 | Update Existing Record | Data Modeling / Storage | Record Operations | Changes field values in a record the user selects or identifies. |
| 110 | Delete Record | Data Modeling / Storage | Record Operations | Removes a record from the table permanently or marks it as deleted if protected. |
| 111 | Create Multiple Records | Data Modeling / Storage | Record Operations | Adds several records to a table at once from a list or imported data. |
| 112 | Create Or Update Record | Data Modeling / Storage | Record Operations | Creates a record if no saved record has the same key value, or updates that record if one does. |
| 113 | Archive Record | Data Modeling / Storage | Record Operations | Moves a record to inactive status without deleting it so it can be restored later. |
| 114 | Restore Archived Record | Data Modeling / Storage | Record Operations | Returns an archived record to active status in the table. |
| 115 | Copy Record | Data Modeling / Storage | Record Operations | Creates a new record by copying an existing one, so the user can change a few fields. |
| 116 | Update Field Across Records | Data Modeling / Storage | Record Operations | Changes one field to a new value in several selected or filtered records at once. |
| 117 | Delete Multiple Records | Data Modeling / Storage | Record Operations | Removes several selected or filtered records at once after a confirmation. |
| 118 | Restore Previous Record Version | Data Modeling / Storage | Record Operations | Puts a record back to an earlier kept version, such as how it was before its last saved change. |
| 119 | Query Saved Records By Criteria | Data Modeling / Storage | Query Building | Reads the saved records of a table that match one or more conditions, joined with AND or OR. |
| 120 | Join Related Tables | Data Modeling / Storage | Query Building | Combines records from two related tables into one result set for display or export. |
| 121 | Search Saved Records By Text | Data Modeling / Storage | Query Building | Finds saved records where any text field contains the words or phrase the user enters. |
| 122 | Group And Summarize Saved Data | Data Modeling / Storage | Query Building | Groups saved records by a field and calculates totals, averages or counts for each group. |
| 123 | Set Primary Key Field | Data Modeling / Storage | Keys and Constraints | Designates a field as the unique identifier that every record must have. |
| 124 | Enforce Unique Field Value | Data Modeling / Storage | Keys and Constraints | Makes the saved table itself refuse two records with the same value in the specified field. |
| 125 | Reference Linked Record | Data Modeling / Storage | Keys and Constraints | Makes sure a field value points to a record that exists in the linked table. |
| 126 | Prevent Accidental Delete | Data Modeling / Storage | Keys and Constraints | Blocks deletion of a record if other records reference it or a condition is met. |
| 127 | Import Records From CSV | Data Modeling / Storage | Import and Export | Loads records into a table from a CSV file the user selects; files that are too large are refused. |
| 128 | Import Records From JSON | Data Modeling / Storage | Import and Export | Reads records from a JSON file the user picks and adds them to the table; files that are too large are refused. |
| 129 | Export Table To CSV | Data Modeling / Storage | Import and Export | Saves a whole table, the records matching a filter, or the records on screen to a CSV file the user picks. |
| 130 | Export Table To JSON | Data Modeling / Storage | Import and Export | Saves a whole table, the records matching a filter, or the records on screen to a JSON file the user picks. |
| 131 | Load Sample Data Set | Data Modeling / Storage | Import and Export | Fills a table with example records so the user can test the app immediately. |

## Logic / Validation (22 cards)

Cards that decide whether data or an action is acceptable, and which rule applies.

| No. | Name | Category | Group | What it does |
| --- | --- | --- | --- | --- |
| 132 | Check Field Is Required | Logic / Validation | Field Validation | Stops the user if a mandatory field is left empty before saving or submitting. |
| 133 | Validate Field Type | Logic / Validation | Field Validation | Confirms a field contains the correct data type such as number, text, or date. |
| 134 | Match Format Pattern | Logic / Validation | Field Validation | Checks a field against a pattern like email address, phone number, or code format. |
| 135 | Validate Number Range | Logic / Validation | Field Validation | Ensures a numeric field falls between a minimum and maximum value. |
| 136 | Check Text Length | Logic / Validation | Field Validation | Verifies a text field meets minimum or maximum character count limits. |
| 137 | Validate Against Allowed List | Logic / Validation | Field Validation | Confirms a field value exists in a predefined list of acceptable options. |
| 138 | Reject Future Date | Logic / Validation | Field Validation | Prevents a date field from being set to a date beyond today. |
| 139 | Compare Two Fields | Logic / Validation | Cross-Field Rules | Checks whether two fields meet a condition like greater than, equal to, or not matching. |
| 140 | Verify Sum Equals Total | Logic / Validation | Cross-Field Rules | Confirms that line item amounts add up to a specified total field. |
| 141 | Require Either Or Field | Logic / Validation | Cross-Field Rules | Ensures at least one of two fields is filled, but not necessarily both. |
| 142 | Require Dependent Field | Logic / Validation | Cross-Field Rules | Makes a second field mandatory, and marks it required on screen, only when a first field has a certain value. |
| 143 | Validate Date Order | Logic / Validation | Cross-Field Rules | Confirms a start date comes before an end date or ship date follows order date. |
| 144 | Prevent Negative Stock | Logic / Validation | Business Rules | Blocks inventory updates that would result in stock quantity falling below zero. |
| 145 | Flag Reorder Level Reached | Logic / Validation | Business Rules | Signals when inventory quantity drops to or below the reorder threshold. |
| 146 | Require Approval Above Amount | Logic / Validation | Business Rules | Marks an order or transaction for manual approval if value exceeds a set limit. |
| 147 | Prevent Duplicate Order | Logic / Validation | Business Rules | Prevents creating a new order when one with the same key details, such as customer, item and date, already exists. |
| 148 | Enforce Lead Time Limit | Logic / Validation | Business Rules | Ensures a delivery or completion date allows enough days from the order date. |
| 149 | Check Valid Status Transition | Logic / Validation | Business Rules | Confirms a status change follows allowed steps like pending to shipped to delivered. |
| 150 | Show Or Hide Field | Logic / Validation | Conditional Display Rules | Decides whether a field appears on screen based on another field or record state. |
| 151 | Enable Or Disable Field | Logic / Validation | Conditional Display Rules | Controls whether a field can be edited depending on conditions like record status. |
| 152 | Confirm Destructive Action | Logic / Validation | Safety Checks | Asks the user to confirm before a high-impact step, such as deleting several records. |
| 153 | Stop On Error Threshold | Logic / Validation | Safety Checks | Halts processing when the count of validation or import errors exceeds a set limit. |

## Triggers / Orchestration (14 cards)

Cards that start a flow or set the order in which steps run, only while the local preview runs.

| No. | Name | Category | Group | What it does |
| --- | --- | --- | --- | --- |
| 154 | Run When Button Pressed | Triggers / Orchestration | User Action Triggers | Starts a flow when the user clicks a button in the application interface. |
| 155 | Run When Form Submitted | Triggers / Orchestration | User Action Triggers | Starts a flow when the user submits a form with input values. |
| 156 | Run When Page Opened | Triggers / Orchestration | User Action Triggers | Starts a flow when the user navigates to a specific page in the application. |
| 157 | Run When Record Selected | Triggers / Orchestration | User Action Triggers | Starts a flow when the user chooses a record from a list or table. |
| 158 | Run On A Timer | Triggers / Orchestration | Timer Triggers | Runs a flow once after a delay, or again and again at a fixed interval, only while the app preview is running. |
| 159 | Run At App Start | Triggers / Orchestration | Timer Triggers | Runs a flow automatically when the app preview begins running. |
| 160 | Run When Record Created | Triggers / Orchestration | Data Event Triggers | Starts a flow when a new record is added while the app preview is running. |
| 161 | Run When Record Changed | Triggers / Orchestration | Data Event Triggers | Starts a flow when an existing record is updated while the app preview is running. |
| 162 | Run When Record Deleted | Triggers / Orchestration | Data Event Triggers | Starts a flow when a record is removed while the app preview is running. |
| 163 | Run When Value Crosses Threshold | Triggers / Orchestration | Data Event Triggers | Starts a flow when a numeric field goes above or below a limit while the app preview is running. |
| 164 | Run Steps In Sequence | Triggers / Orchestration | Flow Control | Runs the connected steps one after another, in the order the user set. |
| 165 | Wait For All Steps To Complete | Triggers / Orchestration | Flow Control | Waits until every branch the flow actually took has finished, then carries on. |
| 166 | Wait For Condition With Timeout | Triggers / Orchestration | Flow Control | Pauses until a condition becomes true or the required time limit runs out, whichever comes first. |
| 167 | Repeat For Each List Item | Triggers / Orchestration | Flow Control | Runs the connected steps once for each record in a list, up to a limit set when building. |

## Integrations / Connectors (20 cards)

Cards that prepare work for a person to do outside the app and take the result back; the app itself makes no outside call.

| No. | Name | Category | Group | What it does |
| --- | --- | --- | --- | --- |
| 168 | Build Order Request | Integrations / Connectors | Payload Preparation | Formats order data into a structured request ready for a person to submit to a supplier. |
| 169 | Build Shipment Notice | Integrations / Connectors | Payload Preparation | Formats shipment details into a notice ready for a person to send to a recipient. |
| 170 | Build Supplier Message | Integrations / Connectors | Payload Preparation | Formats supplier communication data into a message ready for a person to send. |
| 171 | Build Spreadsheet Export | Integrations / Connectors | Payload Preparation | Formats records into a table ready for a person to paste into a spreadsheet. |
| 172 | Build Email Text | Integrations / Connectors | Payload Preparation | Formats data into email-ready text ready for a person to copy and send. |
| 173 | Build Data File | Integrations / Connectors | Payload Preparation | Formats records into a file ready for a person to upload to another tool. |
| 174 | Show Manual Steps | Integrations / Connectors | Human Instructions | Displays step-by-step instructions for a person to follow outside the app. |
| 175 | Show Copyable Text | Integrations / Connectors | Human Instructions | Displays text in a copyable block for a person to paste elsewhere. |
| 176 | Show Action Checklist | Integrations / Connectors | Human Instructions | Displays a checklist of tasks for a person to complete outside the app. |
| 177 | Show Waiting Item | Integrations / Connectors | Human Instructions | Displays an item paused until a person completes an outside action. |
| 178 | Show Pending Reminder | Integrations / Connectors | Human Instructions | Displays a reminder of actions still waiting for a person to complete outside. |
| 179 | Enter Outside Result | Integrations / Connectors | Result Intake | Shows a form where a person types the result of an outside action, such as a reference number or confirmed quantity. |
| 180 | Import Result File | Integrations / Connectors | Result Intake | Lets a person pick and import a result file from an outside action. |
| 181 | Match Result To Item | Integrations / Connectors | Result Intake | Matches a result entered by a person to the waiting item that triggered it. |
| 182 | Reject Invalid Result | Integrations / Connectors | Result Intake | Rejects a result entered by a person if it is stale or does not match. |
| 183 | Reconcile Stale Result | Integrations / Connectors | Result Intake | Shows what changed in a record since an outside action began, and lets the user accept or discard the result. |
| 184 | Resume After Result | Integrations / Connectors | Local Continuation | Continues the flow after a person enters a result from an outside action. |
| 185 | Mark Item Outcome | Integrations / Connectors | Local Continuation | Marks an item as done or failed based on the result a person entered. |
| 186 | Log Outside Action | Integrations / Connectors | Local Continuation | Records a history entry when a person completes an outside action. |
| 187 | Show Still Pending | Integrations / Connectors | Local Continuation | Displays items still waiting for a person to complete outside actions. |

## AI Capabilities (10 cards)

Cards where AI helps build the app or a person brings in an AI answer; the running app never calls AI.

| No. | Name | Category | Group | What it does |
| --- | --- | --- | --- | --- |
| 188 | Suggest Record Layout | AI Capabilities | Build-Time Assistance | Proposes field names and types for a new record table at build time based on the app description. |
| 189 | Draft Sample Records | AI Capabilities | Build-Time Assistance | Generates example rows for testing at build time using the defined record structure. |
| 190 | Propose Field Mappings | AI Capabilities | Build-Time Assistance | Suggests how imported columns match record fields at build time by comparing names and types. |
| 191 | Draft Validation Rules | AI Capabilities | Build-Time Assistance | Creates initial field validation logic at build time from field names and intended data types. |
| 192 | Draft Acceptance Checklist | AI Capabilities | Build-Time Assistance | Proposes, at build time, a checklist of things to try in the finished app, based on the cards used. |
| 193 | Explain App In Plain Words | AI Capabilities | Build-Time Assistance | Writes, at build time, a short plain-language description of how the connected cards work together. |
| 194 | Draft Field Help Text | AI Capabilities | Build-Time Assistance | Writes, at build time, short help text for each input field from its name and type. |
| 195 | Prepare AI Prompt | AI Capabilities | Human-AI Loop | Formats the fields the user picks into a question to copy into an outside AI tool, within a length limit. |
| 196 | Accept AI Answer | AI Capabilities | Human-AI Loop | Receives text the user supplies from an AI tool and stores it in the specified format. |
| 197 | Check Answer Shape | AI Capabilities | Human-AI Loop | Checks, with simple rules, that the answer the user supplies from an AI tool has the expected format and structure before use. |

## Navigation / Output (8 cards)

Cards that move the user between screens and present or hand over final results.

| No. | Name | Category | Group | What it does |
| --- | --- | --- | --- | --- |
| 198 | Open Detail Screen | Navigation / Output | Screen Navigation | Displays the full record view when the user selects an item from a list. |
| 199 | Go Back To List | Navigation / Output | Screen Navigation | Returns the user to the previous list or overview screen. |
| 200 | Open Pop-Up Panel | Navigation / Output | Screen Navigation | Shows a temporary overlay window for quick edits or details without leaving the current screen. |
| 201 | Summary Table | Navigation / Output | Reports | Presents key totals and counts in a table layout for quick overview. |
| 202 | Chart Over Time | Navigation / Output | Reports | Displays a line or bar chart showing how a measure changes across dates or periods. |
| 203 | Grouped Totals View | Navigation / Output | Reports | Shows aggregated counts or sums organized by category or location. |
| 204 | Exception List | Navigation / Output | Reports | Lists low-stock, overdue or out-of-limit records that need attention. |
| 205 | Print-Friendly Page | Navigation / Output | Export and Print | Formats the current view for clean printing, without menus or navigation elements. |

## Where the ideas came from

The categories and groups follow how common low-code and workflow tools split their building blocks, fitted to the framework (Python apps, local single-owner preview, no live outside calls). Sources read:

- [Retool components](https://retool.com/use-case/react-components-library)
- [n8n workflow nodes](https://blog.n8n.io/ai-agentic-workflows/)
- [Node-RED core nodes](https://nodered.org/docs/user-guide/nodes)
- [Appsmith widgets](https://www.appsmith.com/widgets)
- [Budibase components](https://docs.budibase.com/docs/components)
- [Streamlit widgets](https://docs.streamlit.io/develop/api-reference/widgets)
- [Django admin create, read, update, delete](https://www.geeksforgeeks.org/python/crud-operations-in-django-admin/)
- [Zapier workflows](https://zapier.com/workflows)
- [AI workflow patterns in n8n](https://osher.com.au/blog/how-to-build-ai-workflow-n8n/)

Content was rephrased and fitted to this project; no text was copied from these pages.
