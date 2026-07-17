'use client';

import { useState } from 'react';
import { Wrench, Search, Filter, Calendar, Clock, AlertTriangle, CheckCircle, XCircle, Plus, Eye, Edit, BarChart3, ListTodo } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { cn, formatDate } from '@/lib/utils';

interface WorkOrder {
  id: string;
  title: string;
  equipment: string;
  tag: string;
  type: 'preventive' | 'corrective' | 'predictive' | 'emergency';
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'in_progress' | 'completed' | 'cancelled';
  assigned_to: string;
  scheduled_date: string;
  completed_date?: string;
  description: string;
}

const mockWorkOrders: WorkOrder[] = [
  { id: 'WO-2024-045', title: 'Pump P-101 Bearing Replacement', equipment: 'Boiler Feed Pump', tag: 'P-101', type: 'corrective', priority: 'critical', status: 'completed', assigned_to: 'Mike R.', scheduled_date: '2026-07-10', completed_date: '2026-07-10', description: 'Replace bearing and check alignment' },
  { id: 'WO-2024-046', title: 'IDF-201 Vibration Analysis', equipment: 'Induced Draft Fan', tag: 'IDF-201', type: 'predictive', priority: 'high', status: 'in_progress', assigned_to: 'Tech Team', scheduled_date: '2026-07-15', description: 'Perform vibration analysis and report findings' },
  { id: 'WO-2024-047', title: 'Monthly Boiler Inspection', equipment: 'Boiler B-601', tag: 'B-601', type: 'preventive', priority: 'medium', status: 'open', assigned_to: 'Inspection Team', scheduled_date: '2026-07-20', description: 'Monthly visual inspection and tube cleaning' },
  { id: 'WO-2024-048', title: 'Emergency Shutdown Valve Repair', equipment: 'Main Steam Valve', tag: 'V-301', type: 'emergency', priority: 'critical', status: 'open', assigned_to: 'Maintenance Team', scheduled_date: '2026-07-16', description: 'Repair stuck emergency shutdown valve' },
  { id: 'WO-2024-049', title: 'Compressor C-401 Oil Change', equipment: 'Instrument Air Compressor', tag: 'C-401', type: 'preventive', priority: 'low', status: 'completed', assigned_to: 'Mike R.', scheduled_date: '2026-07-05', completed_date: '2026-07-05', description: 'Routine oil change and filter replacement' },
  { id: 'WO-2024-050', title: 'Transformer TRF-901 Thermography', equipment: 'Main Step-up Transformer', tag: 'TRF-901', type: 'predictive', priority: 'high', status: 'in_progress', assigned_to: 'Electrical Team', scheduled_date: '2026-07-14', description: 'Infrared thermography scan of all connections' },
  { id: 'WO-2024-051', title: 'Turbine TG-301 Seal Inspection', equipment: 'Steam Turbine', tag: 'TG-301', type: 'preventive', priority: 'medium', status: 'open', assigned_to: 'Turbine Team', scheduled_date: '2026-07-25', description: 'Inspect and measure shaft seal clearances' },
];

const getPriorityColor = (p: WorkOrder['priority']) => {
  const colors = { critical: 'bg-red-100 text-red-700', high: 'bg-orange-100 text-orange-700', medium: 'bg-yellow-100 text-yellow-700', low: 'bg-green-100 text-green-700' };
  return colors[p];
};

const getStatusColor = (s: WorkOrder['status']) => {
  const colors = { open: 'bg-blue-100 text-blue-700', in_progress: 'bg-yellow-100 text-yellow-700', completed: 'bg-green-100 text-green-700', cancelled: 'bg-gray-100 text-gray-700' };
  return colors[s];
};

const getTypeColor = (t: WorkOrder['type']) => {
  const colors = { preventive: 'bg-blue-100 text-blue-700', corrective: 'bg-orange-100 text-orange-700', predictive: 'bg-purple-100 text-purple-700', emergency: 'bg-red-100 text-red-700' };
  return colors[t];
};

export default function MaintenancePage() {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>(mockWorkOrders);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  const filtered = workOrders.filter(wo => {
    if (searchQuery && !wo.title.toLowerCase().includes(searchQuery.toLowerCase()) && !wo.equipment.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (statusFilter && wo.status !== statusFilter) return false;
    if (typeFilter && wo.type !== typeFilter) return false;
    if (priorityFilter && wo.priority !== priorityFilter) return false;
    return true;
  });

  const stats = {
    total: workOrders.length,
    open: workOrders.filter(w => w.status === 'open').length,
    inProgress: workOrders.filter(w => w.status === 'in_progress').length,
    completed: workOrders.filter(w => w.status === 'completed').length,
    critical: workOrders.filter(w => w.priority === 'critical' && w.status !== 'completed').length,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Maintenance</h1>
              <p className="text-gray-500">Work orders, schedules, and maintenance history</p>
            </div>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Work Order
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-full mx-auto px-6 py-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Total Orders</p><p className="text-3xl font-bold text-gray-900">{stats.total}</p></div><Wrench className="h-10 w-10 text-primary-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Open</p><p className="text-3xl font-bold text-blue-600">{stats.open}</p></div><ListTodo className="h-10 w-10 text-blue-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">In Progress</p><p className="text-3xl font-bold text-yellow-600">{stats.inProgress}</p></div><Clock className="h-10 w-10 text-yellow-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Completed</p><p className="text-3xl font-bold text-green-600">{stats.completed}</p></div><CheckCircle className="h-10 w-10 text-green-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Critical Open</p><p className="text-3xl font-bold text-red-600">{stats.critical}</p></div><AlertTriangle className="h-10 w-10 text-red-600" /></div></CardContent></Card>
        </div>

        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex-1 min-w-[200px] relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input placeholder="Search work orders..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[150px]"><SelectValue placeholder="Type" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Types</SelectItem>
                  <SelectItem value="preventive">Preventive</SelectItem>
                  <SelectItem value="corrective">Corrective</SelectItem>
                  <SelectItem value="predictive">Predictive</SelectItem>
                  <SelectItem value="emergency">Emergency</SelectItem>
                </SelectContent>
              </Select>
              <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                <SelectTrigger className="w-[150px]"><SelectValue placeholder="Priority" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Priorities</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Work Order</TableHead>
                  <TableHead>Equipment</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Assigned To</TableHead>
                  <TableHead>Scheduled</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map(wo => (
                  <TableRow key={wo.id} className="hover:bg-gray-50">
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm">{wo.id}</p>
                        <p className="text-xs text-gray-500">{wo.title}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm">{wo.equipment}</p>
                      <p className="text-xs text-gray-500 font-mono">{wo.tag}</p>
                    </TableCell>
                    <TableCell><Badge variant="secondary" className={getTypeColor(wo.type)}>{wo.type}</Badge></TableCell>
                    <TableCell><Badge variant="secondary" className={getPriorityColor(wo.priority)}>{wo.priority}</Badge></TableCell>
                    <TableCell><Badge variant="secondary" className={getStatusColor(wo.status)}>{wo.status.replace('_', ' ')}</Badge></TableCell>
                    <TableCell className="text-sm">{wo.assigned_to}</TableCell>
                    <TableCell className="text-sm font-mono">{wo.scheduled_date}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="h-7 w-7"><Eye className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7"><Edit className="h-4 w-4" /></Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}