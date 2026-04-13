import React, { useState } from 'react';
import {
  Folder,
  FileText,
  Search,
  Filter,
  LayoutGrid,
  List,
  Plus,
  Star,
  MoreHorizontal,
  Calendar,
  User,
  Trash2,
  Eye
} from 'lucide-react';
import { toast } from 'sonner';
import { handleReviewClick } from '../utils/reviewHandler';

const Documents = () => {
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [activeMenu, setActiveMenu] = useState(null); // Track which item's menu is open (format: "type-id")

  // State for folders
  const [folders, setFolders] = useState([
    { id: 1, name: 'Projects', count: 5, color: 'text-[var(--primary-main)]' },
    { id: 2, name: 'Archives', count: 8, color: 'text-[var(--success-main)]' },
    { id: 3, name: 'Drafts', count: 5, color: 'text-[var(--primary-main)]' },
  ]);

  // State for documents
  const [documents, setDocuments] = useState([
    { id: 1, title: 'Student Registration System.pdf', size: '2.4 MB', date: 'Oct 24, 2025', starred: true },
    { id: 2, title: 'E-Commerce Platform Requirements.docx', size: '1.8 MB', date: 'Oct 23, 2025', starred: false },
    { id: 3, title: 'Healthcare Management System.doc', size: '1.2 MB', date: 'Oct 22, 2025', starred: true },
    { id: 4, title: 'Financial Reporting Tool.pdf', size: '3.1 MB', date: 'Oct 21, 2025', starred: false },
    { id: 5, title: 'Library Management System.docx', size: '2.2 MB', date: 'Oct 20, 2025', starred: true },
  ]);

  // Function to handle document deletion (BR-17: GDPR Right to be Forgotten)
  const handleDeleteDocument = async (docId) => {
    if (window.confirm('Are you sure you want to delete this document? This action cannot be undone.\n\n(GDPR Right to be Forgotten - Data will be permanently removed)')) {
      try {
        // In a real app, this would make an API call to delete the document
        // await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
        console.log(`Deleting document with ID: ${docId}`);

        // Update the documents list to remove the deleted document
        setDocuments(prevDocuments => prevDocuments.filter(doc => doc.id !== docId));
        setActiveMenu(null);

        // Show success message
        toast.success('Document deleted successfully (GDPR compliant)');
      } catch (error) {
        console.error('Error deleting document:', error);
        toast.error('Failed to delete document. Please try again.');
      }
    }
  };

  // Function to handle folder deletion
  const handleDeleteFolder = async (folderId) => {
    if (window.confirm('Are you sure you want to delete this folder? This action cannot be undone.')) {
      try {
        // In a real app, this would make an API call to delete the folder
        // await fetch(`/api/folders/${folderId}`, { method: 'DELETE' });
        console.log(`Deleting folder with ID: ${folderId}`);

        // Update the folders list to remove the deleted folder
        setFolders(prevFolders => prevFolders.filter(folder => folder.id !== folderId));
        setActiveMenu(null);

        // Show success message
        toast.success('Folder deleted successfully');
      } catch (error) {
        console.error('Error deleting folder:', error);
        toast.error('Failed to delete folder. Please try again.');
      }
    }
  };

  // Function to toggle the menu for a specific document/folder
  const toggleMenu = (itemId, type = 'document') => {
    const menuKey = `${type}-${itemId}`;
    setActiveMenu(activeMenu === menuKey ? null : menuKey);
  };

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-4 sm:py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header Row */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
            <div className="mb-6 sm:mb-0">
              <h1 className="text-3xl font-bold text-[var(--text-primary)]">Documents</h1>
              <p className="text-[var(--text-secondary)] mt-1">Manage all your requirements in one place</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search Input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)]" />
                <input
                  type="text"
                  placeholder="Search documents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full sm:w-64 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent bg-[var(--card-bg)] text-[var(--text-primary)]"
                />
              </div>

              {/* Filter Button */}
              <button className="flex items-center space-x-2 px-3 py-2 border border-[var(--card-border)] rounded-lg text-[var(--text-secondary)] hover:bg-[var(--surface-bg)] transition-colors">
                <Filter className="h-4 w-4" />
                <span>Filter</span>
              </button>

              {/* View Toggle */}
              <div className="flex border border-[var(--card-border)] rounded-lg">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'bg-[var(--primary-main)] text-white' : 'text-[var(--text-secondary)] hover:bg-[var(--surface-bg)]'} rounded-l-lg transition-colors`}
                >
                  <LayoutGrid className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 ${viewMode === 'list' ? 'bg-[var(--primary-main)] text-white' : 'text-[var(--text-secondary)] hover:bg-[var(--surface-bg)]'} rounded-r-lg transition-colors`}
                >
                  <List className="h-4 w-4" />
                </button>
              </div>

              {/* New Document Button */}
              <button className="bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-[var(--primary-hover)] transition-colors">
                <Plus className="h-4 w-4" />
                <span>New Document</span>
              </button>
            </div>
          </div>

          {/* Folders Section */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">Folders</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
              {folders.map((folder) => (
                <div
                  key={folder.id}
                  className="bg-[var(--card-bg)] p-4 sm:p-6 rounded-xl border border-[var(--card-border)] shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="bg-[var(--surface-bg)] p-3 rounded-lg mr-4">
                        <Folder className={`h-6 w-6 ${folder.color}`} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-[var(--text-primary)]">{folder.name}</h3>
                        <p className="text-sm text-[var(--text-secondary)]">{folder.count} documents</p>
                      </div>
                    </div>
                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleMenu(folder.id, 'folder');
                        }}
                        className="text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </button>

                      {activeMenu === `folder-${folder.id}` && (
                        <div className="absolute right-0 mt-2 w-40 bg-[var(--card-bg)] rounded-md shadow-lg py-1 z-10 border border-[var(--card-border)] tooltip">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteFolder(folder.id);
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-[var(--error-main)] hover:bg-[var(--error-light)] flex items-center"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete Folder
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* New Folder Card */}
              <div 
                onClick={() => {
                  // Show prompt for folder name
                  const folderName = prompt('Enter folder name:');
                  if (folderName) {
                    // Add new folder to the list
                    setFolders(prevFolders => [
                      ...prevFolders,
                      {
                        id: Math.max(...prevFolders.map(f => f.id), 0) + 1, // Generate new ID
                        name: folderName,
                        count: 0,
                        color: 'text-[var(--primary-main)]'
                      }
                    ]);
                    
                    // Show success message
                    toast.success('Folder created successfully!');
                  }
                }}
                className="border-2 border-dashed border-[var(--card-border)] rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer hover:border-[var(--primary-main)] hover:bg-[var(--surface-bg)] transition-colors"
              >
                <div className="bg-[var(--surface-bg)] p-3 rounded-lg mb-3">
                  <Plus className="h-6 w-6 text-[var(--primary-main)]" />
                </div>
                <p className="text-sm font-medium text-[var(--text-secondary)]">New Folder</p>
              </div>
            </div>
          </div>

          {/* All Documents Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">All Documents</h2>
              <p className="text-sm text-[var(--text-secondary)]">{documents.length} documents</p>
            </div>

            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="bg-[var(--card-bg)] p-6 rounded-xl border border-[var(--card-border)] shadow-sm hover:shadow-md transition-all cursor-pointer table-row"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center">
                        <div className="bg-[var(--surface-bg)] p-3 rounded-lg mr-4">
                          <FileText className="h-5 w-5 text-[var(--primary-main)]" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-[var(--text-primary)]">{doc.title}</h3>
                          <p className="text-sm text-[var(--text-secondary)]">{doc.size}</p>
                        </div>
                      </div>
                      <div className="relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleMenu(doc.id, 'document');
                          }}
                          className="text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </button>

                        {activeMenu === `document-${doc.id}` && (
                          <div className="absolute right-0 mt-2 w-40 bg-[var(--card-bg)] rounded-md shadow-lg py-1 z-10 border border-[var(--card-border)] tooltip">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteDocument(doc.id);
                              }}
                              className="w-full text-left px-4 py-2 text-sm text-[var(--error-main)] hover:bg-[var(--error-light)] flex items-center"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete Document
                            </button>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-6">
                      <button className="text-[var(--text-secondary)] hover:text-[var(--warning-main)] transition-colors">
                        {doc.starred ? (
                          <Star className="h-4 w-4 fill-current text-[var(--warning-main)]" />
                        ) : (
                          <Star className="h-4 w-4 text-[var(--text-secondary)]" />
                        )}
                      </button>
                      <div className="flex items-center text-sm text-[var(--text-secondary)]">
                        <Calendar className="h-4 w-4 mr-1" />
                        {doc.date}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)] shadow-sm overflow-hidden">
                <table className="min-w-full divide-y divide-[var(--card-border)]">
                  <thead className="bg-[var(--card-bg)]">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Size</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--card-border)]">
                    {documents.map((doc) => (
                      <tr key={doc.id} className="hover:bg-[var(--surface-bg)] transition-colors cursor-pointer table-row">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="bg-[var(--surface-bg)] p-2 rounded-lg mr-3">
                              <FileText className="h-5 w-5 text-[var(--primary-main)]" />
                            </div>
                            <div>
                              <div className="text-sm font-medium text-[var(--text-primary)]">{doc.title}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">{doc.size}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {doc.date}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                          <div className="flex items-center space-x-2">
                            <button className="text-[var(--text-secondary)] hover:text-[var(--warning-main)] transition-colors">
                              {doc.starred ? (
                                <Star className="h-4 w-4 fill-current text-[var(--warning-main)]" />
                              ) : (
                                <Star className="h-4 w-4 text-[var(--text-secondary)]" />
                              )}
                            </button>
                            <div className="relative">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleMenu(doc.id, 'document');
                                }}
                                className="text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors"
                              >
                                <MoreHorizontal className="h-4 w-4" />
                              </button>

                              {activeMenu === `document-${doc.id}` && (
                                <div className="absolute right-0 mt-2 w-40 bg-[var(--card-bg)] rounded-md shadow-lg py-1 z-10 border border-[var(--card-border)] tooltip">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteDocument(doc.id);
                                    }}
                                    className="w-full text-left px-4 py-2 text-sm text-[var(--error-main)] hover:bg-[var(--error-light)] flex items-center"
                                  >
                                    <Trash2 className="h-4 w-4 mr-2" />
                                    Delete Document
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Documents;