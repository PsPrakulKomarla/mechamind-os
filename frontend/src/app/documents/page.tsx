'use client';

import { useState, useCallback } from 'react';
import { FileText, Upload, Search, Filter, Download, Trash2, Eye, MoreHorizontal, Grid, List, ChevronDown, File, Image, Video, FileSpreadsheet, FileArchive } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { cn, formatDateTime } from '@/lib/utils';

interface Document {
  id: string;
  title: string;
  type: 'pdf' | 'image' | 'video' | 'spreadsheet' | 'archive' | 'other';
  category: string;
  status: 'processed' | 'processing' | 'failed' | 'pending';
  size: string;
  pages: number;
  uploaded_by: string;
  uploaded_at: string;
  tags: string[];
}

const mockDocuments: Document[] = [
  { id: '1', title: 'Pump P-101 Maintenance Manual.pdf', type: 'pdf', category: 'maintenance', status: 'processed', size: '12.4 MB', pages: 145, uploaded_by: 'Sarah M.', uploaded_at: '2026-07-15T10:30:00Z', tags: ['pump', 'maintenance', 'P-101'] },
  { id: '2', title: 'Boiler B-601 Operating Procedure.pdf', type: 'pdf', category: 'procedure', status: 'processed', size: '8.2 MB', pages: 89, uploaded_by: 'Mike R.', uploaded_at: '2026-07-14T14:20:00Z', tags: ['boiler', 'operating', 'procedure'] },
  { id: '3', title: 'Compressor Layout Drawing Rev C.dwg', type: 'image', category: 'drawing', status: 'processed', size: '3.1 MB', pages: 1, uploaded_by: 'Design Team', uploaded_at: '2026-07-13T09:15:00Z', tags: ['compressor', 'drawing', 'layout'] },
  { id: '4', title: 'Safety Training Video - Confined Space.mp4', type: 'video', category: 'safety', status: 'processing', size: '456 MB', pages: 0, uploaded_by: 'Safety Dept', uploaded_at: '2026-07-12T16:45:00Z', tags: ['safety', 'training', 'confined-space'] },
  { id: '5', title: 'Equipment Inspection Checklist.xlsx', type: 'spreadsheet', category: 'inspection', status: 'processed', size: '2.8 MB', pages: 12, uploaded_by: 'QA Team', uploaded_at: '2026-07-11T11:00:00Z', tags: ['inspection', 'checklist', 'equipment'] },
  { id: '6', title: 'OISD-116 Guidelines.pdf', type: 'pdf', category: 'compliance', status: 'processed', size: '5.6 MB', pages: 67, uploaded_by: 'Compliance Bot', uploaded_at: '2026-07-10T08:30:00Z', tags: ['compliance', 'oisd', 'guidelines'] },
  { id: '7', title: 'Vibration Analysis Report - IDF-201.pdf', type: 'pdf', category: 'report', status: 'processed', size: '4.3 MB', pages: 34, uploaded_by: 'Maintenance Team', uploaded_at: '2026-07-09T13:00:00Z', tags: ['vibration', 'analysis', 'IDF-201'] },
  { id: '8', title: 'Piping Isometric Drawing P-ID-101.dwg', type: 'image', category: 'drawing', status: 'pending', size: '1.8 MB', pages: 1, uploaded_by: 'Design Team', uploaded_at: '2026-07-08T10:00:00Z', tags: ['piping', 'isometric', 'P-ID-101'] },
  { id: '9', title: 'Annual Maintenance Schedule 2026.pdf', type: 'pdf', category: 'maintenance', status: 'failed', size: '15.2 MB', pages: 200, uploaded_by: 'Planning Dept', uploaded_at: '2026-07-07T15:30:00Z', tags: ['maintenance', 'schedule', 'annual'] },
  { id: '10', title: 'Equipment Photos - Turbine Hall.zip', type: 'archive', category: 'reference', status: 'processed', size: '78.5 MB', pages: 0, uploaded_by: 'Field Team', uploaded_at: '2026-07-06T09:45:00Z', tags: ['photos', 'turbine', 'reference'] },
];

const categories = ['maintenance', 'procedure', 'drawing', 'safety', 'inspection', 'compliance', 'report', 'reference'];
const documentTypes = ['pdf', 'image', 'video', 'spreadsheet', 'archive', 'other'];
const statuses = ['processed', 'processing', 'failed', 'pending'];

const getTypeIcon = (type: Document['type']) => {
  switch (type) {
    case 'pdf': return <FileText className="h-8 w-8 text-red-500" />;
    case 'image': return <Image className="h-8 w-8 text-blue-500" />;
    case 'video': return <Video className="h-8 w-8 text-purple-500" />;
    case 'spreadsheet': return <FileSpreadsheet className="h-8 w-8 text-green-500" />;
    case 'archive': return <FileArchive className="h-8 w-8 text-orange-500" />;
    default: return <File className="h-8 w-8 text-gray-500" />;
  }
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>(mockDocuments);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

  const filteredDocs = documents.filter((doc) => {
    if (searchQuery && !doc.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (categoryFilter && doc.category !== categoryFilter) return false;
    if (typeFilter && doc.type !== typeFilter) return false;
    if (statusFilter && doc.status !== statusFilter) return false;
    return true;
  });

  const stats = {
    total: documents.length,
    processed: documents.filter(d => d.status === 'processed').length,
    processing: documents.filter(d => d.status === 'processing').length,
    failed: documents.filter(d => d.status === 'failed').length,
  };

  const getStatusBadge = (status: Document['status']) => {
    const colors = {
      processed: 'bg-green-100 text-green-700',
      processing: 'bg-blue-100 text-blue-700',
      failed: 'bg-red-100 text-red-700',
      pending: 'bg-gray-100 text-gray-700',
    };
    return <Badge variant="secondary" className={colors[status]}>{status}</Badge>;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
              <p className="text-gray-500">Manage and search industrial documents, drawings, and manuals</p>
            </div>
            <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Document
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>Upload Document</DialogTitle>
                </DialogHeader>
                <div className="py-6">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-primary-500 transition-colors cursor-pointer">
                    <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-600 font-medium">Drop files here or click to browse</p>
                    <p className="text-sm text-gray-500 mt-1">PDF, Images, Videos, Spreadsheets (Max 100MB)</p>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
                  <Button disabled>Upload</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </header>

      {/* Stats */}
      <div className="max-w-full mx-auto px-6 py-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Documents</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
                </div>
                <FileText className="h-10 w-10 text-primary-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Processed</p>
                  <p className="text-3xl font-bold text-green-600">{stats.processed}</p>
                </div>
                <FileText className="h-10 w-10 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Processing</p>
                  <p className="text-3xl font-bold text-blue-600">{stats.processing}</p>
                </div>
                <FileText className="h-10 w-10 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Failed</p>
                  <p className="text-3xl font-bold text-red-600">{stats.failed}</p>
                </div>
                <FileText className="h-10 w-10 text-red-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex-1 min-w-[200px] relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[160px]"><SelectValue placeholder="Category" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Categories</SelectItem>
                  {categories.map(c => <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[140px]"><SelectValue placeholder="Type" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Types</SelectItem>
                  {documentTypes.map(t => <SelectItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px]"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  {statuses.map(s => <SelectItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</SelectItem>)}
                </SelectContent>
              </Select>
              <div className="flex items-center border rounded-lg">
                <Button variant={viewMode === 'grid' ? 'secondary' : 'ghost'} size="icon" className="h-9 w-9 rounded-r-none" onClick={() => setViewMode('grid')}>
                  <Grid className="h-4 w-4" />
                </Button>
                <Button variant={viewMode === 'list' ? 'secondary' : 'ghost'} size="icon" className="h-9 w-9 rounded-l-none" onClick={() => setViewMode('list')}>
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Document Grid/List */}
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredDocs.map((doc) => (
              <Card key={doc.id} className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    {getTypeIcon(doc.type)}
                    {getStatusBadge(doc.status)}
                  </div>
                  <h3 className="font-medium text-gray-900 text-sm line-clamp-2 mb-1">{doc.title}</h3>
                  <p className="text-xs text-gray-500 mb-3">{doc.size} • {doc.pages > 0 ? `${doc.pages} pages` : 'N/A'}</p>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {doc.tags.slice(0, 3).map(tag => (
                      <Badge key={tag} variant="secondary" className="text-xs bg-gray-100 text-gray-600">{tag}</Badge>
                    ))}
                    {doc.tags.length > 3 && <span className="text-xs text-gray-400">+{doc.tags.length - 3}</span>}
                  </div>
                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <span className="text-xs text-gray-400">{doc.uploaded_by}</span>
                    <span className="text-xs text-gray-400">{formatDateTime(doc.uploaded_at)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Uploaded</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDocs.map((doc) => (
                    <TableRow key={doc.id} className="hover:bg-gray-50">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          {getTypeIcon(doc.type)}
                          <div>
                            <p className="font-medium text-sm">{doc.title}</p>
                            <p className="text-xs text-gray-500">{doc.pages > 0 ? `${doc.pages} pages` : 'N/A'}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell><Badge variant="secondary" className="bg-blue-100 text-blue-700">{doc.type.toUpperCase()}</Badge></TableCell>
                      <TableCell className="capitalize">{doc.category}</TableCell>
                      <TableCell>{getStatusBadge(doc.status)}</TableCell>
                      <TableCell className="text-sm">{doc.size}</TableCell>
                      <TableCell className="text-sm text-gray-500">{formatDateTime(doc.uploaded_at)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="icon" className="h-7 w-7"><Eye className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" className="h-7 w-7"><Download className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-red-600"><Trash2 className="h-4 w-4" /></Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}