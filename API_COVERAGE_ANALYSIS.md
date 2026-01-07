# Atera API v3 Coverage Analysis

## Currently Implemented ✓ (15 data types)

### Core Entities
- ✅ **Customers** (`/api/v3/customers`)
- ✅ **Contacts** (`/api/v3/contacts`) - Fixed: uses EndUserID
- ✅ **Agents** (`/api/v3/agents`)
- ✅ **Alerts** (`/api/v3/alerts`)
- ✅ **Tickets** (`/api/v3/tickets`)
- ✅ **Contracts** (`/api/v3/contracts`)
- ✅ **Invoices** (`/api/v3/billing/invoices`)
- ✅ **Departments** (`/api/v3/departments`)

### Device Types
- ✅ **SNMP Devices** (`/api/v3/devices/snmpdevices`)
- ✅ **TCP Devices** (`/api/v3/devices/tcpdevices`)
- ✅ **HTTP Devices** (`/api/v3/devices/httpdevices`)
- ✅ **Generic Devices** (`/api/v3/devices/genericdevices`)

### Knowledge & Billing
- ✅ **Knowledge Base** (`/api/v3/knowledgebases`)
- ✅ **Products** (`/api/v3/rates/products`)
- ✅ **Expenses** (`/api/v3/rates/expenses`)

---

## Missing Data - High Priority 🔴

### 1. **Account Information** (NEW)
- **Endpoint**: `/api/v3/account`
- **Why**: Provides company details, plan type, timezone, location
- **Fields**: AccountID, Country, CompanyName, State, TimeZoneName, Plan, etc.
- **Impact**: Important for multi-tenant scenarios

### 2. **Ticket Comments** (NESTED)
- **Endpoint**: `/api/v3/tickets/{ticketId}/comments`
- **Why**: Critical for ticket history and communication records
- **Fields**: Date, Comment, TechnicianContactID, EndUserID, IsInternal
- **Impact**: **HIGH** - Missing complete ticket context

### 3. **Ticket Work Hours** (NESTED)
- **Endpoint**: `/api/v3/tickets/{ticketId}/workhoursrecords`
- **Why**: Billing and time tracking data
- **Fields**: StartWorkHour, EndWorkHour, TechnicianContactID, Billiable, OnCustomerSite, RateAmount
- **Impact**: **HIGH** - Critical for billing analysis

### 4. **Agent Patch Management** (NESTED)
- **Endpoints**:
  - `/api/v3/agents/{deviceGuid}/installed-patches`
  - `/api/v3/agents/{deviceGuid}/available-patches`
- **Why**: Security compliance and patch tracking
- **Fields**: Name, Class, KBId, InstallDate, Status
- **Impact**: **HIGH** - Security/compliance reporting

### 5. **Custom Field Definitions** (NEW)
- **Endpoint**: `/api/v3/customvalues/customfields`
- **Why**: Schema for custom fields across all entities
- **Fields**: Name, DataType, Target, PossibleValues
- **Impact**: MEDIUM - Enables custom field value export

---

## Missing Data - Medium Priority 🟡

### 6. **Custom Field Values** (NESTED)
- **Endpoints** for each entity type:
  - `/api/v3/customvalues/ticketfields/{ticketId}`
  - `/api/v3/customvalues/customerfields/{customerId}`
  - `/api/v3/customvalues/contactfields/{contactId}`
  - `/api/v3/customvalues/contractfields/{contractId}`
  - `/api/v3/customvalues/agentfields/{agentId}`
  - `/api/v3/customvalues/snmpfields/{snmpDeviceId}`
  - `/api/v3/customvalues/tcpfields/{tcpDeviceId}`
  - `/api/v3/customvalues/httpfields/{httpDeviceId}`
  - `/api/v3/customvalues/genericfields/{genericDeviceId}`
- **Why**: Captures organization-specific metadata
- **Impact**: MEDIUM - Depends on custom field usage

### 7. **Ticket Durations** (NESTED)
- **Endpoints**:
  - `/api/v3/tickets/{ticketId}/billableduration`
  - `/api/v3/tickets/{ticketId}/nonbillableduration`
  - `/api/v3/tickets/billableworkhourssiteduration` (bulk)
- **Why**: Detailed time tracking for billing
- **Fields**: OnSiteDurationHours, OffSiteDurationHours, OnSLADurationHours, etc.
- **Impact**: MEDIUM - Already have basic durations in ticket object

### 8. **Ticket Attachments** (NESTED)
- **Endpoint**: `/api/v3/tickets/{ticketId}/attachments`
- **Why**: Complete ticket documentation
- **Returns**: URLs to attachments
- **Impact**: MEDIUM - May be large files

---

## Missing Data - Low Priority 🟢

### 9. **Last Modified Tickets** (FILTER)
- **Endpoint**: `/api/v3/tickets/lastmodified`
- **Why**: Incremental sync capability
- **Impact**: LOW - Current full sync works fine

### 10. **Status Modified Tickets** (FILTER)
- **Endpoint**: `/api/v3/tickets/statusmodified`
- **Why**: Track resolved/closed tickets
- **Impact**: LOW - Can filter from main tickets endpoint

---

## Field Coverage Issues ⚠️

Need to verify we're capturing ALL fields from responses:

### Contacts (FIXED)
- ✅ Changed from `ContactID` to `EndUserID`
- ⚠️ **Missing fields**: `MobilePhone`, `DepartmentID`, `DepartmentName`

### Agents
- ⚠️ **Missing fields**: `AgentVersion`, `Favorite`, `ThresholdID`, `ReportedFromIP`, `Display`, `Sound`, `ProcessorCoresCount`, `Vendor`, `VendorSerialNumber`, `VendorBrandModel`, `ProductName`, `HardwareDisks`, `WindowsSerialNumber`, `OfficeSP`, `OfficeOEM`, `OfficeSerialNumber`, `OSNum`, `DeviceType`

### Tickets
- ⚠️ **Missing fields**: `TicketResolvedDate`, `TechnicianFirstCommentDate`, `FirstResponseDueDate`, `ClosedTicketDueDate`, `FirstComment`, `LastEndUserCommentTimestamp`, `LastTechnicianCommentTimestamp`, `CustomerBusinessNumber`, `TechnicianFullName`, `TechnicianEmail`, `ContractID`

### Alerts
- ⚠️ **Missing fields**: `Code`, `ThresholdValue2-5`, `SnoozedEndDate`, `AdditionalInfo`, `ArchivedDate`, `FolderID`, `PollingCyclesCount`

### Contracts
- ⚠️ **Missing nested contract types**: RetainerFlatFee, Hourly, BlockHours, BlockMoney, RemoteMonitoring, OnlineBackup, ProjectOneTimeFee, ProjectHourlyRate

### Invoices
- ⚠️ **Missing fields**: LineItems array, From/To contact details

---

## Recommended Implementation Priority

### Phase 1 - Critical Missing Data 🔴
1. **Ticket Comments** - Essential for ticket analysis
2. **Ticket Work Hours** - Critical for billing
3. **Agent Patches** - Security/compliance
4. **Account Info** - Basic account context

### Phase 2 - Complete Field Coverage ⚠️
5. Update all existing models to capture missing fields
6. Add custom field definitions
7. Add custom field values for all entity types

### Phase 3 - Enhanced Features 🟡
8. Ticket durations (detailed)
9. Ticket attachments
10. Incremental sync support

---

## Database Schema Impact

### New Tables Needed:
- `TicketComment` - One-to-many with Ticket
- `TicketWorkHour` - One-to-many with Ticket
- `AgentInstalledPatch` - One-to-many with Agent
- `AgentAvailablePatch` - One-to-many with Agent
- `CustomFieldDefinition` - Standalone
- `CustomFieldValue` - Polymorphic relation to all entities
- `Account` - Single record

### Updated Tables:
- `Contact` - Add mobile_phone, department_id, department_name
- `Agent` - Add ~20 missing fields
- `Ticket` - Add ~10 missing fields
- `Alert` - Add ~8 missing fields
- `Contract` - Add contract type details
- `Invoice` - Add line items structure

---

## Estimated Additions

- **New Entities**: 7 (Account, TicketComment, TicketWorkHour, AgentInstalledPatch, AgentAvailablePatch, CustomFieldDefinition, CustomFieldValue)
- **Updated Entities**: 6 (Contact, Agent, Ticket, Alert, Contract, Invoice)
- **New API Methods**: ~15
- **New Sync Functions**: ~10
- **New Database Models**: 7
- **Updated Database Models**: 6

**Total Coverage**: Currently 15/22 entity types (~68%)
**After Phase 1**: 19/22 (~86%)
**After Phase 2**: 22/22 (100%)
